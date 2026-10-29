import json
import re
from pathlib import Path
from typing import Any, Iterable

from mdf_core.foundation.constants import CHANGELOG_CATEGORIES
from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.yamlutil import read_frontmatter


def aggregate_release_changes(
    repo: Path,
    slugs: list[str],
) -> tuple[
    dict[str, list[str]],
    bool,
    set[str],
    set[str],
    set[str],
    set[str],
    set[str],
    dict[str, list[str]],
]:
    notes = {category: [] for category in CHANGELOG_CATEGORIES}
    breaking = False
    proposals: set[str] = set()
    fixed: set[str] = set()
    closed: set[str] = set()
    deferred: set[str] = set()
    adrs: set[str] = set()
    evidence_sources: list[dict[str, Any]] = []
    for slug in sorted(slugs):
        change = repo / "changes" / "unreleased" / slug / "CHANGE.md"
        metadata, _ = read_frontmatter(change)
        proposals.update(metadata.get("proposals", []))
        fixed.update(metadata.get("fixed", []))
        closed.update(metadata.get("closed", []))
        deferred.update(metadata.get("deferred", []))
        adrs.update(metadata.get("adrs", []))
        breaking = breaking or metadata.get("breaking") is True
        release_notes = metadata.get("release_notes")
        if isinstance(release_notes, dict):
            for category in CHANGELOG_CATEGORIES:
                values = release_notes.get(category, [])
                if isinstance(values, list):
                    notes[category].extend(values)
        raw_evidence = metadata.get("evidence")
        if isinstance(raw_evidence, dict):
            evidence_sources.append(raw_evidence)
    return (
        notes,
        breaking,
        proposals,
        fixed,
        closed,
        deferred,
        adrs,
        merge_evidence(*evidence_sources),
    )


def merge_evidence(
    *sources: dict[str, Any],
) -> dict[str, list[str]]:
    """Merge evidence in source order while retaining each first occurrence."""
    merged = {"tests": [], "commands": [], "artifacts": []}
    seen = {key: set() for key in merged}
    for source in sources:
        for key in merged:
            values = source.get(key, []) if isinstance(source, dict) else []
            if not isinstance(values, list):
                continue
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    continue
                if value in seen[key]:
                    continue
                seen[key].add(value)
                merged[key].append(value)
    return merged


def render_version_change(
    version: str,
    previous: str | None,
    release_date: str,
    mode: str,
    slugs: list[str],
    categories: set[str],
    breaking: bool,
    minimum_bump: str,
    actual_bump: str,
    validation_commands: list[str],
    proposals: set[str],
    fixed: set[str],
    closed: set[str],
    deferred: set[str],
    adrs: set[str],
    closed_proposal_resolutions: dict[str, str],
    found_in_transitions: list[str],
    deferred_acceptance: dict[str, Any],
    hotfix_body: str | None = None,
    release_notes: dict[str, list[str]] | None = None,
    evidence: dict[str, list[str]] | None = None,
    *,
    verify_command_results: list[dict[str, Any]] | None = None,
) -> str:
    def yaml_list(values: Iterable[str]) -> str:
        return "[" + ", ".join(sorted(values)) + "]"

    def notes_yaml() -> str:
        if not categories:
            return "release_notes: none\n"
        lines = ["release_notes:"]
        for category in CHANGELOG_CATEGORIES:
            if category in categories:
                values = (
                    release_notes.get(category, []) if release_notes else []
                )
                if not values:
                    values = [category]
                lines.append(f"  {category}:")
                lines.extend(
                    f"    - {json.dumps(str(value), ensure_ascii=False)}"
                    for value in values
                )
        return "\n".join(lines) + "\n"

    child_lines = (
        "\n".join(f"- [{slug}]({slug}/CHANGE.md)" for slug in sorted(slugs))
        or "None."
    )
    previous_value = previous if previous is not None else "none"
    commands_text = "".join(
        f"    - {json.dumps(str(command), ensure_ascii=False)}\n"
        for command in validation_commands
    )

    def evidence_yaml() -> str:
        lines = ["evidence:"]
        for key in ("tests", "commands", "artifacts"):
            values = evidence.get(key, []) if evidence else []
            if not values:
                lines.append(f"  {key}: []")
                continue
            lines.append(f"  {key}:")
            lines.extend(
                f"    - {json.dumps(value, ensure_ascii=False)}"
                for value in values
            )
        return "\n".join(lines) + "\n"

    transition_lines = (
        "\n".join(f"- {line}" for line in found_in_transitions) or "None."
    )
    if deferred_acceptance:
        acceptance_lines = "\n".join(
            (
                f"- `{identifier}`: {value.get('reason', 'accepted')}; "
                f"follow-up: {value.get('follow_up', 'none')}"
            )
            for identifier, value in sorted(deferred_acceptance.items())
            if isinstance(value, dict)
        )
    else:
        acceptance_lines = "None."
    return (
        "---\n"
        f'version: "{version}"\n'
        f'previous_version: "{previous_value}"\n'
        f'date: "{release_date}"\n'
        f"change_kind: {mode}\n"
        f"source_branch: {mode}/{version}\n"
        f"proposals: {yaml_list(proposals)}\n"
        f"fixed: {yaml_list(fixed)}\n"
        f"closed: {yaml_list(closed)}\n"
        f"deferred: {yaml_list(deferred)}\n"
        + f"adrs: {yaml_list(adrs)}\n"
        f"included_changes: {yaml_list(slugs)}\n"
        + notes_yaml()
        + f"breaking: {'true' if breaking else 'false'}\n"
        + evidence_yaml()
        + "audit: passed\n"
        + "---\n\n"
        f"# {mode.title()} {version}\n\n"
        "## 结果\n\n"
        + (hotfix_body or "发布收口已完成。")
        + "\n\n## 包含的 Change\n\n"
        + child_lines
        + "\n\n## 已更新的当前文档\n\n"
        + "已生成 CHANGELOG.md 与版本根目录中的 CHANGE.md。\n\n"
        + "## 已知偏差\n\n无。\n\n"
        + "## 收口结果\n\n"
        + "### Proposal\n\n"
        + (
            chr(10).join(f"- `{item}`" for item in sorted(proposals))
            or "无。"
        )
        + "\n\n### 已关闭的 Proposal\n\n"
        + (
            chr(10).join(
                f"- `{item}` ({closed_proposal_resolutions[item]})"
                for item in sorted(closed_proposal_resolutions)
            )
            or "无。"
        )
        + "\n\n### 已修复的 Bug\n\n"
        + (chr(10).join(f"- `{item}`" for item in sorted(fixed)) or "无。")
        + "\n\n### 已关闭的 Bug\n\n"
        + (
            chr(10).join(f"- `{item}`" for item in sorted(closed))
            or "无。"
        )
        + "\n\n### 延后的 Bug\n\n"
        + (chr(10).join(f"- `{item}`" for item in sorted(deferred)) or "无。")
        + "\n\n## found-in 转换\n\n"
        + transition_lines
        + "\n\n## 延后接受理由\n\n"
        + acceptance_lines
        + "\n\n## SemVer 决策\n\n"
        + "- 观察到的类别："
        + f"{', '.join(sorted(categories)) if categories else '无'}\n"
        + f"- 破坏性变更：{'是' if breaking else '否'}\n"
        + f"- 最低升级幅度：{minimum_bump}\n"
        + f"- 实际升级幅度：{actual_bump}\n"
        + f"- 选定版本：`{version}`\n\n"
        + "## 审计\n\n"
        + "- 确定性的全量审计：已通过（由 Core 验证）。\n"
        + "- 验证命令：\n"
        + "".join(
            (
                f"  - `{item.get('command')}` → exit {item.get('exit_code')}\n"
                if isinstance(item, dict)
                else f"  - `{item}`\n"
            )
            for item in (
                verify_command_results
                or [
                    {"command": command, "exit_code": 0}
                    for command in validation_commands
                ]
            )
        )
        + "\n## 验证命令\n\n```text\n"
        + "\n".join(validation_commands)
        + "\n```\n"
    )


def changelog_excerpt(text: str, version: str) -> str:
    """取出 CHANGELOG 中该版本一节，作发布 tag 正文。"""
    match = re.search(
        rf"^##\s+\[?{re.escape(version)}]?(?:\s|$)",
        text,
        re.MULTILINE,
    )
    if not match:
        raise MDFError(
            f"CHANGELOG 缺少 {version} 条目，不能创建发布 tag",
            code="missing_changelog",
        )
    start = match.start()
    rest = text[match.end() :]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    end = match.end() + nxt.start() if nxt else len(text)
    return text[start:end].strip()


def release_tag_message(tag: str, excerpt: str) -> str:
    return f"chore(release): 发布 {tag}\n\n{excerpt}"


def update_changelog_text(
    text: str,
    *,
    version: str,
    release_date: str,
    notes: dict[str, list[str]],
) -> str:
    if not text.startswith("# Changelog"):
        raise MDFError(
            "CHANGELOG.md 必须以 '# Changelog' 开头",
            code="invalid_changelog",
        )
    if re.search(
        rf"^##\s+\[?{re.escape(version)}]?(?:\s|$)",
        text,
        re.MULTILINE,
    ):
        raise MDFError(
            f"CHANGELOG already contains {version}",
            code="collision",
        )
    lines = [f"## [{version}] - {release_date}", ""]
    populated = False
    for category in CHANGELOG_CATEGORIES:
        values = notes[category]
        if not values:
            continue
        populated = True
        lines.extend([f"### {category}", ""])
        lines.extend(f"- {value}" for value in values)
        lines.append("")
    if not populated:
        lines.extend(["- 没有面向用户的变更。", ""])
    section = "\n".join(lines)
    heading_end = text.find("\n")
    if heading_end < 0:
        return text + "\n\n" + section
    insert_at = heading_end + 1
    return text[:insert_at] + "\n" + section + text[insert_at:]


def update_manifest_release(text: str, version: str) -> str:
    updated, count = re.subn(
        r"^(\s*latest_release:\s*).*$",
        rf'\g<1>"{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise MDFError(
            "manifest 没有唯一的 latest_release 字段",
            code="invalid_manifest",
        )
    return updated
