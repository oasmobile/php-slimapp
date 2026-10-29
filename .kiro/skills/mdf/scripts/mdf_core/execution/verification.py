"""项目验证入口：lint、build 与 quick/smoke/release；命令来自 `.mdf/modules.yaml`。"""
import re
from pathlib import Path

from mdf_core.foundation.errors import MDFError

STEPS = ("lint", "build")
SUITES = ("quick", "smoke", "release")
ENTRIES = (*STEPS, *SUITES)
ALL_ENTRIES = (*ENTRIES, "coverage")
# full 是全部 test case 的概念，没有入口；保留其名不给 named suite。
RESERVED = (*ALL_ENTRIES, "full")
DEFAULT_BUDGETS = {"quick": 30, "smoke": 300}
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MIGRATE_HINT = "；用 $mdf migrate 收敛到当前契约"


class Verification:
    """验证视图：默认按 module 串行展开；repo 级 verification 可覆写单入口。"""

    def __init__(
        self,
        module_commands: dict[str, dict[str, str | dict]],
        overrides: dict[str, str | dict],
        budgets: dict[str, int],
    ):
        self.module_commands = module_commands
        self.overrides = overrides
        self.budgets = budgets

    def budget(self, name):
        return self.budgets.get(name, DEFAULT_BUDGETS.get(name))

    def plan(self, suite):
        names = [*STEPS, "quick"] + ([suite] if suite != "quick" else [])
        items = []
        for entry in names:
            items.extend(self._items_for_entry(entry))
        return items

    def _items_for_entry(self, entry: str) -> list[dict]:
        budget = self.budget(entry)
        if entry == "coverage":
            entries = [(None, self.overrides[entry])] if entry in self.overrides else [
                (name, commands[entry]) for name, commands in sorted(self.module_commands.items()) if entry in commands
            ]
            return [{"id": f"coverage:{name}" if name else "coverage", "entry": entry,
                     "command": config["command"], "coverage_targets": config["targets"],
                     "budget": None, **({"module": name} if name else {})} for name, config in entries]
        if entry in self.overrides:
            return [
                {
                    "id": entry,
                    "command": self.overrides[entry],
                    "budget": budget,
                    "entry": entry,
                }
            ]
        if not self.module_commands:
            raise MDFError(
                f"验证入口 {entry} 既无 module 命令也无 repo 覆写",
                code="invalid_verification",
            )
        return [
            {
                "id": f"{entry}:{module}",
                "command": self.module_commands[module][entry],
                "budget": budget,
                "entry": entry,
                "module": module,
            }
            for module in sorted(self.module_commands)
        ]

    def config(self):
        return {
            "overrides": dict(sorted(self.overrides.items())),
            "modules": {
                name: dict(commands)
                for name, commands in sorted(self.module_commands.items())
            },
            "budgets": dict(sorted(self.budgets.items())),
        }


def required_suite(kind):
    # verify branch 默认：release → release；其余交付分支 → smoke
    if kind == "release":
        return "release"
    if kind in {"feature", "bugfix", "hotfix"}:
        return "smoke"
    raise MDFError("验证 suite 需要 Gitflow 交付分支", code="unsupported_branch")


def required_suites(kind):
    return ["quick", required_suite(kind)]


def recorded_suites(record):
    raw = record.get("suites")
    if not isinstance(raw, list) or any(not isinstance(name, str) for name in raw):
        return []
    return raw


def suites_cover(recorded, required):
    """按 quick ⊆ smoke ⊆ release 判断覆盖；named suite 只按名称匹配。"""
    covered = set(recorded)
    for index, suite in enumerate(SUITES):
        if suite in covered:
            covered.update(SUITES[:index])
    return covered >= set(required)


def parse_suite_names(raw):
    if not isinstance(raw, list) or not raw:
        raise MDFError(
            "named suite 必须为非空名称列表", code="invalid_delivery_suite"
        )
    seen = []
    for name in raw:
        if (
            not isinstance(name, str)
            or not NAME_RE.fullmatch(name)
            or name in RESERVED
            or name in seen
        ):
            raise MDFError(
                "named suite 名称无效、重复或占用 lint/build/quick/smoke/release/coverage/full",
                code="invalid_delivery_suite",
            )
        seen.append(name)
    return seen


def validate_verification(raw):
    """完整五集命令视图（初始化 CLI 等）；全部视为 repo 覆写，不展开 module。"""
    if (
        not isinstance(raw, dict)
        or set(raw) - {*ENTRIES, "coverage", "budgets"}
        or set(ENTRIES) - set(raw)
    ):
        raise MDFError(
            "verification 必须且只能声明 lint、build、quick、smoke、release "
            "与可选 coverage、budgets" + MIGRATE_HINT,
            code="invalid_verification",
        )
    overrides = {}
    for name in ENTRIES:
        value = raw[name]
        if not isinstance(value, str) or not value.strip():
            raise MDFError(
                f"verification.{name} 必须为非空命令",
                code="invalid_verification",
            )
        overrides[name] = value.strip()
    if "coverage" in raw:
        from mdf_core.execution.coverage import parse_coverage
        overrides["coverage"] = parse_coverage(raw["coverage"], "verification.coverage")
    budgets = raw.get("budgets", {})
    if (
        not isinstance(budgets, dict)
        or set(budgets) - set(SUITES)
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            for value in budgets.values()
        )
    ):
        raise MDFError(
            "verification.budgets 只接受 quick、smoke、release 的正整数秒数",
            code="invalid_verification",
        )
    return Verification({}, overrides, dict(budgets))


def repo_verification(repo: Path):
    """从 `.mdf/modules.yaml` 构建 repo 级 Verification（默认按 module 串行展开）。"""
    from mdf_core.execution.modules import load_modules

    return load_modules(repo).verification()


def manifest_verification(manifest):
    """优先由调用方改用 repo_verification(repo)；保留 manifest 兼容路径。"""
    if isinstance(manifest, dict) and "verification" in manifest:
        return validate_verification(manifest.get("verification"))
    raise MDFError(
        "验证命令已迁至 .mdf/modules.yaml" + MIGRATE_HINT,
        code="invalid_verification",
    )


def parse_budgets(raw):
    budgets = {}
    for value in raw:
        name, sep, seconds = value.partition("=")
        if not sep or name in budgets or not seconds.isdigit():
            raise MDFError(
                "--budget 必须为 <suite>=<秒数>", code="invalid_verification"
            )
        budgets[name] = int(seconds)
    return budgets


def parse_named_commands(meta: dict) -> tuple[list[str], bool]:
    """从 named suite 文档 frontmatter 解析 commands 与 parallel。"""
    parallel = meta.get("parallel", False)
    if not isinstance(parallel, bool):
        raise MDFError(
            "named suite parallel 必须为布尔",
            code="invalid_named_suite",
        )
    if "commands" in meta:
        raw = meta["commands"]
        if not isinstance(raw, list) or not raw:
            raise MDFError(
                "named suite commands 必须为非空列表",
                code="invalid_named_suite",
            )
        commands: list[str] = []
        for item in raw:
            if not isinstance(item, str) or not item.strip():
                raise MDFError(
                    "named suite commands 项必须为非空字符串",
                    code="invalid_named_suite",
                )
            commands.append(item.strip())
        return commands, parallel
    if "command" in meta:
        value = meta["command"]
        if not isinstance(value, str) or not value.strip():
            raise MDFError(
                "named suite command 必须为非空字符串",
                code="invalid_named_suite",
            )
        return [value.strip()], parallel
    raise MDFError(
        "named suite 文档 frontmatter 需要 commands 或 command",
        code="invalid_named_suite",
    )
