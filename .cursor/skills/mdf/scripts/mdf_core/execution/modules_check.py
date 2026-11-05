"""modules.yaml 校验、渲染与按 module 拆开的命令入口。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.workspace.gitutil import run
from mdf_core.execution.modules import (
    MODULES_PATH,
    SUITE_DOC_DIR,
    Module,
    ModulesConfig,
    load_modules,
    match,
    modules_path,
)
from mdf_core.foundation.paths import path_stays_in_repo
from mdf_core.execution.verification import DEFAULT_BUDGETS, SUITES


def validate_modules(repo: Path, findings: list[Finding]) -> ModulesConfig | None:
    path = modules_path(repo)
    if not path.is_file():
        add_finding(
            findings,
            "modules.missing",
            f"缺少 {MODULES_PATH}",
            MODULES_PATH,
        )
        return None
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        add_finding(
            findings,
            "modules.symlink",
            f"{MODULES_PATH} 必须是普通文件",
            MODULES_PATH,
        )
        return None
    try:
        config = load_modules(repo)
    except MDFError as exc:
        add_finding(findings, "modules.invalid", str(exc), MODULES_PATH)
        return None
    tracked = _tracked_relpaths(repo)
    for module in config.modules.values():
        _validate_sourceset(module, findings)
        _validate_named_docs(repo, module, findings)
        _validate_suite_inclusion(module, tracked, findings)
    return config


def render_modules_yaml(
    *,
    module_name: str = "default",
    sourceset: list[str],
    lint: str,
    build: str,
    quick: str,
    smoke: str,
    release: str,
    budgets: dict[str, int] | None = None,
    named: list[str] | None = None,
    tests_quick: list[str] | None = None,
    tests_smoke: list[str] | None = None,
    tests_release: list[str] | None = None,
) -> str:
    from mdf_core.foundation.yamlutil import yaml_quote

    quick_tests = tests_quick or ["tests/**"]
    smoke_tests = tests_smoke or list(quick_tests)
    release_tests = tests_release or list(smoke_tests)
    lines = ["modules:", f"  {module_name}:", "    sourceset:"]
    for pattern in sourceset:
        lines.append(f"      - {yaml_quote(pattern)}")
    lines.append("    ignore: []")
    lines.append(f"    lint: {yaml_quote(lint)}")
    lines.append(f"    build: {yaml_quote(build)}")
    for suite_name, command, tests in (
        ("quick", quick, quick_tests),
        ("smoke", smoke, smoke_tests),
        ("release", release, release_tests),
    ):
        lines.append(f"    {suite_name}:")
        lines.append(f"      command: {yaml_quote(command)}")
        lines.append("      tests:")
        for pattern in tests:
            lines.append(f"        - {yaml_quote(pattern)}")
    named = named or []
    if named:
        lines.append("    named:")
        for item in named:
            lines.append(f"      - {yaml_quote(item)}")
    else:
        lines.append("    named: []")
    if budgets:
        lines.append("budgets:")
        for name, seconds in budgets.items():
            lines.append(f"  {name}: {seconds}")
    return "\n".join(lines) + "\n"


def module_commands(
    config: ModulesConfig, names: list[str], entry: str
) -> list[dict[str, Any]]:
    """按 module 拆开的入口，供 smart 执行；id 为 entry:module。"""
    budget = None
    if entry in SUITES:
        budget = config.budgets.get(entry, DEFAULT_BUDGETS.get(entry))
    if entry in config.overrides:
        return [
            {
                "id": entry,
                "entry": entry,
                "command": config.overrides[entry],
                "budget": budget,
            }
        ]
    return [
        {
            "id": f"{entry}:{name}",
            "module": name,
            "entry": entry,
            "command": config.get(name).command(entry),
            "budget": budget,
        }
        for name in sorted(names)
    ]


def _match_tests(tracked: list[str], patterns: tuple[str, ...]) -> set[str]:
    return {
        path
        for path in tracked
        if any(match(path, pattern) for pattern in patterns)
    }


def _validate_suite_inclusion(
    module: Module, tracked: list[str], findings: list[Finding]
) -> None:
    """每个 module 内匹配文件须满足 quick ⊆ smoke ⊆ release。"""
    if not tracked:
        return
    quick = _match_tests(tracked, module.quick.tests)
    smoke = _match_tests(tracked, module.smoke.tests)
    release = _match_tests(tracked, module.release.tests)
    if quick and not quick <= smoke:
        add_finding(
            findings,
            "modules.suite_inclusion",
            f"module {module.name}: quick.tests 匹配集必须 ⊆ smoke.tests",
            MODULES_PATH,
        )
    if smoke and not smoke <= release:
        add_finding(
            findings,
            "modules.suite_inclusion",
            f"module {module.name}: smoke.tests 匹配集必须 ⊆ release.tests",
            MODULES_PATH,
        )


def _tracked_relpaths(repo: Path) -> list[str]:
    result = run(["git", "ls-files", "-z"], cwd=repo, check=False)
    if result.returncode:
        return []
    return [raw.replace("\\", "/") for raw in result.stdout.split("\0") if raw]


def _validate_sourceset(module: Module, findings: list[Finding]) -> None:
    for pattern in module.sourceset:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            add_finding(
                findings,
                "modules.sourceset",
                f"sourceset 必须是仓库相对 glob: {pattern}",
                MODULES_PATH,
            )


def _validate_named_docs(
    repo: Path, module: Module, findings: list[Finding]
) -> None:
    from mdf_core.foundation.yamlutil import read_frontmatter
    from mdf_core.execution.verification import parse_named_commands

    for suite in module.named:
        rel = f"{SUITE_DOC_DIR}/{suite}.md"
        path = repo / rel
        if not path.is_file() or path.is_symlink():
            add_finding(
                findings,
                "modules.named_doc",
                f"named suite {suite} 需要独立文档 {rel}",
                rel,
            )
            continue
        try:
            meta, body = read_frontmatter(path)
            parse_named_commands(meta)
        except MDFError as exc:
            add_finding(
                findings,
                "modules.named_doc_command",
                f"named suite 文档命令无效: {exc}",
                rel,
            )
            body = path.read_text(encoding="utf-8")
        lower = body.lower()
        text = body
        if "目的" not in text and "purpose" not in lower:
            add_finding(
                findings,
                "modules.named_doc_purpose",
                f"named suite 文档须写明测试目的: {rel}",
                rel,
            )
        if (
            "testcase" not in lower
            and "测试用例" not in text
            and "构成" not in text
        ):
            add_finding(
                findings,
                "modules.named_doc_cases",
                f"named suite 文档须写明 testcase 构成: {rel}",
                rel,
            )
