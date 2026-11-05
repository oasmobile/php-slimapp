"""`.mdf/modules.yaml`：module 的 sourceset、ignore 与分套件验证入口。"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.paths import path_stays_in_repo
from mdf_core.execution.verification import DEFAULT_BUDGETS, ENTRIES, NAME_RE, RESERVED, SUITES, Verification
from mdf_core.foundation.yamlutil import parse_yaml

MODULES_PATH = ".mdf/modules.yaml"
SUITE_DOC_DIR = "docs/system/testing"


@dataclass(frozen=True)
class SuiteEntry:
    command: str
    tests: tuple[str, ...]
    parallel: bool = False


@dataclass(frozen=True)
class IgnoreRule:
    pattern: str
    reason: str


@dataclass(frozen=True)
class SizeLimits:
    max_file_lines: int = 1000
    max_package_files: int = 50
    split_percent: int = 70

    def target(self, limit: int) -> int:
        return limit * self.split_percent // 100


@dataclass(frozen=True)
class Module:
    name: str
    sourceset: tuple[str, ...]
    ignore: tuple[IgnoreRule, ...]
    lint: str
    build: str
    quick: SuiteEntry
    smoke: SuiteEntry
    release: SuiteEntry
    named: tuple[str, ...]
    size_limits: SizeLimits = field(default_factory=SizeLimits)
    coverage: dict | None = None

    def suite(self, name: str) -> SuiteEntry:
        if name == "quick":
            return self.quick
        if name == "smoke":
            return self.smoke
        if name == "release":
            return self.release
        raise KeyError(name)

    def command(self, name: str) -> str:
        if name == "lint":
            return self.lint
        if name == "build":
            return self.build
        return self.suite(name).command


@dataclass
class ModulesConfig:
    modules: dict[str, Module] = field(default_factory=dict)
    budgets: dict[str, int] = field(default_factory=dict)
    overrides: dict[str, str | dict] = field(default_factory=dict)

    def names(self) -> list[str]:
        return sorted(self.modules)

    def get(self, name: str) -> Module:
        if name not in self.modules:
            raise MDFError(f"未知 module: {name}", code="unknown_module")
        return self.modules[name]

    def named_owner(self) -> dict[str, str]:
        ownership: dict[str, str] = {}
        for module in self.modules.values():
            for suite in module.named:
                ownership[suite] = module.name
        return ownership

    def verification(self) -> Verification:
        """默认按 module 串行展开；顶层 verification 覆写的入口用单命令。"""
        module_commands = {
            name: {entry: self.modules[name].command(entry) for entry in ENTRIES}
            for name in self.names()
        }
        for name, module in self.modules.items():
            if module.coverage is not None:
                module_commands[name]["coverage"] = module.coverage
        budgets = dict(DEFAULT_BUDGETS)
        budgets.update(self.budgets)
        return Verification(module_commands, dict(self.overrides), budgets)

    def modules_for_paths(self, repo: Path, paths: list[str]) -> list[str]:
        hit: set[str] = set()
        for raw in paths:
            rel = raw.replace("\\", "/")
            for module in self.modules.values():
                if path_ignored(rel, module):
                    continue
                if any(match(rel, pattern) for pattern in module.sourceset):
                    hit.add(module.name)
        return sorted(hit)

    def owns(self, rel: str) -> bool:
        return any(match(rel, pattern) for module in self.modules.values() for pattern in module.sourceset)

    def is_ignored(self, rel: str) -> bool:
        owners = [m for m in self.modules.values() if any(match(rel, p) for p in m.sourceset)]
        return bool(owners) and all(path_ignored(rel, m) for m in owners)

    def ignore_matches(self, rel: str, owner: str, rule: IgnoreRule) -> bool:
        return match(rel, rule.pattern) and (any(
            match(rel, pattern) for pattern in self.modules[owner].sourceset))

    def size_policies(self, paths: list[str]) -> list[tuple[str, SizeLimits]]:
        policies: dict[str, SizeLimits] = {}
        for path in paths:
            matched = False
            for name, module in self.modules.items():
                if any(match(path, pattern) for pattern in module.sourceset):
                    matched = True
                    if not path_ignored(path, module):
                        policies[name] = module.size_limits
            if not matched:
                policies[""] = SizeLimits()
        return sorted(policies.items())

    def all_ignore_rules(self) -> list[tuple[str, IgnoreRule]]:
        rules: list[tuple[str, IgnoreRule]] = []
        for module in self.modules.values():
            for rule in module.ignore:
                rules.append((module.name, rule))
        return rules


def modules_path(repo: Path) -> Path:
    return repo / MODULES_PATH


def load_modules(repo: Path) -> ModulesConfig:
    path = modules_path(repo)
    if not path.is_file():
        raise MDFError(
            f"缺少 {MODULES_PATH}",
            code="modules_missing",
        )
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        raise MDFError(
            f"{MODULES_PATH} 必须是普通文件",
            code="modules_invalid",
        )
    raw = parse_yaml(path.read_text(encoding="utf-8"))
    return parse_modules(raw)


def parse_modules(raw: Any) -> ModulesConfig:
    if not isinstance(raw, dict):
        raise MDFError("modules.yaml 根必须是 mapping", code="modules_invalid")
    extra = set(raw) - {"modules", "budgets", "verification"}
    if extra:
        raise MDFError(
            f"modules.yaml 含未知键: {sorted(extra)}",
            code="modules_invalid",
        )
    modules_raw = raw.get("modules")
    if not isinstance(modules_raw, dict) or not modules_raw:
        raise MDFError(
            "modules.yaml 需要非空 modules",
            code="modules_invalid",
        )
    budgets = _parse_budgets(raw.get("budgets", {}))
    overrides = _parse_overrides(raw.get("verification"))
    modules: dict[str, Module] = {}
    seen_named: set[str] = set()
    for name, body in modules_raw.items():
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise MDFError(
                f"module 名称无效: {name!r}",
                code="modules_invalid",
            )
        if name in RESERVED:
            raise MDFError(
                f"module 名称占用保留字: {name}",
                code="modules_invalid",
            )
        module = _parse_module(name, body, seen_named)
        modules[name] = module
    return ModulesConfig(modules=modules, budgets=budgets, overrides=overrides)


def _parse_overrides(raw: Any) -> dict[str, str | dict]:
    """顶层 verification：可只覆写五集中的若干项；空 mapping / 缺省 = 无覆写。"""
    if raw is None or raw == {}:
        return {}
    if not isinstance(raw, dict):
        raise MDFError(
            "verification 必须是 mapping",
            code="modules_invalid",
        )
    extra = set(raw) - {*ENTRIES, "coverage"}
    if extra:
        raise MDFError(
            f"verification 含未知键: {sorted(extra)}",
            code="modules_invalid",
        )
    overrides: dict[str, str | dict] = {}
    for name, value in raw.items():
        if name == "coverage":
            from mdf_core.execution.coverage import parse_coverage
            overrides[name] = parse_coverage(value, "verification.coverage")
            continue
        overrides[name] = _nonempty_command(
            value, f"verification.{name}"
        )
    return overrides


def match(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix.rstrip("/") + "/")
    return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(
        Path(path).name, pattern
    )


def path_ignored(rel: str, module: Module) -> bool:
    return (any(match(rel, pattern) for pattern in module.sourceset)
            and any(match(rel, rule.pattern) for rule in module.ignore))


def _parse_budgets(raw: Any) -> dict[str, int]:
    if raw is None or raw == {}:
        return {}
    if (
        not isinstance(raw, dict)
        or set(raw) - set(SUITES)
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            for value in raw.values()
        )
    ):
        raise MDFError(
            "budgets 只接受 quick、smoke、release 的正整数秒数",
            code="modules_invalid",
        )
    return dict(raw)


def _parse_module(name: str, body: Any, seen_named: set[str]) -> Module:
    if not isinstance(body, dict):
        raise MDFError(
            f"module {name} 必须是 mapping",
            code="modules_invalid",
        )
    allowed = {
        "sourceset",
        "ignore",
        "lint",
        "build",
        "quick",
        "smoke",
        "release",
        "named",
        "size_limits",
        "coverage",
    }
    extra = set(body) - allowed
    if extra:
        raise MDFError(
            f"module {name} 含未知键: {sorted(extra)}",
            code="modules_invalid",
        )
    missing = {"sourceset", "lint", "build", "quick", "smoke", "release"} - set(
        body
    )
    if missing:
        raise MDFError(
            f"module {name} 缺少字段: {sorted(missing)}",
            code="modules_invalid",
        )
    sourceset = _string_list(body["sourceset"], f"module {name}.sourceset")
    if not sourceset:
        raise MDFError(
            f"module {name}.sourceset 不能为空",
            code="modules_invalid",
        )
    ignore = _parse_ignore(f'module {name}', body.get("ignore", []))
    lint = _nonempty_command(body["lint"], f"module {name}.lint")
    build = _nonempty_command(body["build"], f"module {name}.build")
    quick = _parse_suite(name, "quick", body["quick"])
    smoke = _parse_suite(name, "smoke", body["smoke"])
    release = _parse_suite(name, "release", body["release"])
    named = _parse_named(name, body.get("named", []), seen_named)
    return Module(
        name=name,
        sourceset=tuple(sourceset),
        ignore=tuple(ignore),
        lint=lint,
        build=build,
        quick=quick,
        smoke=smoke,
        release=release,
        named=tuple(named),
        size_limits=_parse_size_limits(name, body.get("size_limits", {})),
        coverage=_module_coverage(name, body),
    )


def _module_coverage(name, body):
    from mdf_core.execution.coverage import parse_coverage

    return parse_coverage(body["coverage"], f"module {name}.coverage") if "coverage" in body else None


def _parse_size_limits(name: str, raw: Any) -> SizeLimits:
    label = f"module {name}.size_limits"
    fields = {"max_file_lines", "max_package_files", "split_percent"}
    if not isinstance(raw, dict) or set(raw) - fields:
        raise MDFError(f"{label} 必须是仅含 {sorted(fields)} 的 mapping", code="modules_invalid")
    if any(type(value) is not int or value <= 0 for value in raw.values()):
        raise MDFError(f"{label} 各字段必须是正整数", code="modules_invalid")
    limits = SizeLimits(**raw)
    if limits.split_percent > 100 or min(limits.target(limits.max_file_lines),
                                          limits.target(limits.max_package_files)) < 1:
        raise MDFError(f"{label} split_percent 须在 1–100，且拆分目标至少为 1", code="modules_invalid")
    return limits


def _parse_ignore(name: str, raw: Any) -> list[IgnoreRule]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise MDFError(
            f"{name}.ignore 必须是列表",
            code="modules_invalid",
        )
    rules: list[IgnoreRule] = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) != {"pattern", "reason"}:
            raise MDFError(
                f"{name}.ignore 项需要 pattern 与 reason",
                code="modules_invalid",
            )
        pattern = entry["pattern"]
        reason = entry["reason"]
        if not isinstance(pattern, str) or not pattern.strip():
            raise MDFError(
                f"{name}.ignore.pattern 必须非空",
                code="modules_invalid",
            )
        if not isinstance(reason, str) or not reason.strip():
            raise MDFError(
                f"{name}.ignore.reason 必须非空",
                code="modules_invalid",
            )
        rules.append(IgnoreRule(pattern.strip(), reason.strip()))
    return rules


def _parse_suite(module: str, suite: str, raw: Any) -> SuiteEntry:
    label = f"module {module}.{suite}"
    if isinstance(raw, str):
        raise MDFError(
            f"{label} 必须是含 command 与 tests 的 mapping",
            code="modules_invalid",
        )
    if not isinstance(raw, dict):
        raise MDFError(
            f"{label} 必须是含 command 与 tests 的 mapping",
            code="modules_invalid",
        )
    allowed = {"command", "tests", "parallel"}
    if set(raw) - allowed or "command" not in raw or "tests" not in raw:
        raise MDFError(
            f"{label} 必须含 command 与 tests，可选 parallel",
            code="modules_invalid",
        )
    command = _nonempty_command(raw["command"], f"{label}.command")
    tests = _string_list(raw["tests"], f"{label}.tests")
    if not tests:
        raise MDFError(f"{label}.tests 不能为空", code="modules_invalid")
    parallel = raw.get("parallel", False)
    if not isinstance(parallel, bool):
        raise MDFError(
            f"{label}.parallel 必须为布尔",
            code="modules_invalid",
        )
    return SuiteEntry(command=command, tests=tuple(tests), parallel=parallel)


def _parse_named(module: str, raw: Any, seen: set[str]) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise MDFError(
            f"module {module}.named 必须是列表",
            code="modules_invalid",
        )
    names: list[str] = []
    for item in raw:
        if (
            not isinstance(item, str)
            or not NAME_RE.fullmatch(item)
            or item in RESERVED
        ):
            raise MDFError(
                f"module {module}.named 含无效名: {item!r}",
                code="modules_invalid",
            )
        if item in seen:
            raise MDFError(
                f"named suite 重复登记: {item}",
                code="modules_invalid",
            )
        seen.add(item)
        names.append(item)
    return names


def _nonempty_command(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise MDFError(f"{label} 必须为非空命令", code="modules_invalid")
    return raw.strip()


def _string_list(raw: Any, label: str) -> list[str]:
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise MDFError(f"{label} 必须是字符串列表", code="modules_invalid")
    return [item.strip() for item in raw if item.strip()]
