import re
from pathlib import Path

from mdf_core.foundation.constants import CHANGE_KINDS, MARKER_RE, contains_unreleased_sentinel
from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.workspace.gitutil import branch_details
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.foundation.textutil import stable_semver
from mdf_core.inspection.validate_objects import required_sections
from mdf_core.foundation.yamlutil import read_frontmatter


def validate_change_file(
    repo: Path,
    path: Path,
    findings: list[Finding],
    *,
    expected_slug: str,
    root: bool = False,
) -> None:
    rel = relative(repo, path)
    try:
        metadata, body = read_frontmatter(path)
    except MDFError as exc:
        add_finding(findings, "change.frontmatter", str(exc), rel)
        return
    change_kind = metadata.get("change_kind")
    if change_kind not in CHANGE_KINDS:
        add_finding(
            findings,
            "change.kind",
            "CHANGE requires change_kind feature, bugfix, fix, release, hotfix, or adhoc",
            rel,
        )
    source_branch = metadata.get("source_branch")
    if not isinstance(source_branch, str):
        add_finding(
            findings,
            "change.source_branch",
            "CHANGE requires source_branch",
            rel,
        )
    elif not root and source_branch == "develop":
        if change_kind not in {"feature", "bugfix", "fix"}:
            add_finding(
                findings,
                "change.kind",
                "develop-sourced CHANGE requires change_kind feature, bugfix, or fix",
                rel,
            )
    else:
        try:
            details = branch_details(source_branch)
        except MDFError as exc:
            add_finding(findings, "change.source_branch", str(exc), rel)
        else:
            expected_kinds = (
                {"release", "hotfix"} if root else {"feature", "bugfix", "adhoc"}
            )
            if (
                not details["supported"]
                or details["kind"] not in expected_kinds
            ):
                add_finding(
                    findings,
                    "change.source_branch",
                    "CHANGE source_branch does not match its directory role",
                    rel,
                )
            elif change_kind != details["kind"] and not (
                details["kind"] == "adhoc" and change_kind == "fix"
            ):
                add_finding(
                    findings,
                    "change.kind",
                    "change_kind must match source_branch",
                    rel,
                )
            elif not root and details["kind"] != "adhoc" and details["slug"] != expected_slug:
                add_finding(
                    findings,
                    "change.slug",
                    "CHANGE directory slug does not match source_branch",
                    rel,
                )
    if root:
        if change_kind not in {"release", "hotfix"}:
            add_finding(
                findings,
                "change.kind",
                "Version-root CHANGE must be release or hotfix",
                rel,
            )
        if (
            not isinstance(metadata.get("version"), str)
            or metadata.get("version") != expected_slug
        ):
            add_finding(
                findings,
                "change.version",
                "Version-root CHANGE version must equal its directory",
                rel,
            )
        previous = metadata.get("previous_version")
        if previous not in (None, "none") and stable_semver(previous) is None:
            add_finding(
                findings,
                "change.previous_version",
                "previous_version must be a stable SemVer or none",
                rel,
            )
        if metadata.get("audit") != "passed":
            add_finding(
                findings,
                "change.audit",
                "Version-root CHANGE audit must be passed",
                rel,
            )
        included = metadata.get("included_changes")
        if not isinstance(included, list) or any(
            not isinstance(item, str) for item in included
        ):
            add_finding(
                findings,
                "change.included",
                "included_changes must be a string list",
                rel,
            )
    for key in ("proposals", "fixed", "closed", "deferred", "adrs"):
        if not isinstance(metadata.get(key), list):
            add_finding(
                findings,
                "change.links",
                f"{key} must be a list",
                rel,
            )
    adhoc = change_kind == "adhoc"
    if isinstance(source_branch, str):
        try:
            adhoc = adhoc or branch_details(source_branch)["kind"] == "adhoc"
        except MDFError:
            pass
    if adhoc and metadata.get("proposals") != []:
        add_finding(findings, "change.proposals", "adhoc Change 的 proposals 必须为空列表", rel)
    if "bugs" in metadata:
        add_finding(
            findings,
            "change.bugs_renamed",
            "请使用 fixed、closed 或 deferred，而不是 bugs",
            rel,
        )
    bug_lists = [metadata.get(key) for key in ("fixed", "closed", "deferred")]
    bug_ids = [
        item
        for values in bug_lists
        if isinstance(values, list)
        for item in values
    ]
    if any(not isinstance(item, str) for item in bug_ids):
        add_finding(
            findings, "change.links", "Bug outcome 列表元素必须是字符串", rel
        )
        bug_ids = [item for item in bug_ids if isinstance(item, str)]
    if len(bug_ids) != len(set(bug_ids)):
        add_finding(
            findings,
            "change.bug_duplicate",
            "同一 Bug ID 只能出现在一个 outcome 列表中",
            rel,
        )
    release_notes = metadata.get("release_notes")
    categories = {
        "Added",
        "Changed",
        "Deprecated",
        "Removed",
        "Fixed",
        "Security",
    }
    if release_notes == "none":
        pass
    elif isinstance(release_notes, dict):
        unknown = set(release_notes) - categories
        populated = [
            value
            for value in release_notes.values()
            if isinstance(value, list) and value
        ]
        if (
            unknown
            or not populated
            or any(
                not isinstance(value, list)
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in value
                )
                for value in release_notes.values()
            )
        ):
            add_finding(
                findings,
                "change.release_notes",
                "release_notes must use non-empty Keep a Changelog categories",
                rel,
            )
    else:
        add_finding(
            findings,
            "change.release_notes",
            "release_notes must be the scalar none or a category mapping",
            rel,
        )
    if not isinstance(metadata.get("breaking"), bool):
        add_finding(
            findings, "change.breaking", "breaking must be boolean", rel
        )
    elif (
        isinstance(release_notes, dict)
        and "Removed" in release_notes
        and metadata.get("breaking") is not True
    ):
        add_finding(
            findings,
            "change.removed_breaking",
            "A Removed release note requires breaking: true",
            rel,
        )
    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict):
        add_finding(
            findings, "change.evidence", "evidence must be a mapping", rel
        )
    else:
        fixed = evidence.get("range")
        if "range" in evidence and (not isinstance(fixed, dict)
                                  or not {"base", "source_head"} <= fixed.keys()
                                  or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value)
                                         for value in fixed.values())
                                  or set(fixed) - {"base", "source_head", "target_head"}):
            add_finding(findings, "change.range", "evidence.range 需要完整 commit hash 范围", rel)
        for key in ("tests", "commands", "artifacts"):
            values = evidence.get(key)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip()
                for value in values
            ):
                add_finding(
                    findings,
                    "change.evidence",
                    f"evidence.{key} 必须是非空字符串元素组成的列表",
                    rel,
                )
    if contains_unreleased_sentinel(metadata):
        add_finding(
            findings,
            "version.sentinel_scope",
            "unreleased is forbidden in CHANGE metadata",
            rel,
        )
    if MARKER_RE.search(body):
        add_finding(
            findings,
            "change.marker",
            "CHANGE contains an unresolved template marker",
            rel,
        )
    sections = [
        "结果",
        "已更新的当前文档",
        "已知偏差",
    ]
    if root:
        sections.extend(
            [
                "包含的 Change",
                "收口结果",
                "found-in 转换",
                "SemVer 决策",
                "审计",
                "验证命令",
            ]
        )
    required_sections(body, sections, rel, findings)


def validate_version_change_file(
    repo: Path, path: Path, findings: list[Finding], version: str
) -> None:
    validate_change_file(repo, path, findings, expected_slug=version, root=True)
