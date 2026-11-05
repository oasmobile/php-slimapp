import re
from pathlib import Path
from typing import Any, Iterable
from mdf_core.foundation.constants import (
    BUG_REJECT_REASONS,
    BUG_SEVERITIES,
    BUG_STATUSES,
    EPOCH_RE,
    MARKER_RE,
    OBJECT_FILE_RE,
    contains_unreleased_sentinel,
    is_unreleased_sentinel,
)
from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.foundation.textutil import is_object_id_slug, stable_semver
from mdf_core.foundation.yamlutil import read_frontmatter
def iter_object_files(repo: Path, kind: str) -> Iterable[Path]:
    root = repo / "docs" / ("proposals" if kind == "proposal" else "bugs")
    if (
        not root.is_dir()
        or root.is_symlink()
        or not path_stays_in_repo(repo, root)
    ):
        return []
    # Validate misplaced prp-*/bug-* Markdown instead of silently ignoring it.
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".md", ".html"}
        and not path.name.endswith(".review.html")
        and not path.is_symlink()
        and path_stays_in_repo(repo, path)
    )
def required_sections(
    body: str, headings: Iterable[str], rel: str, findings: list[Finding]
) -> None:
    for heading in headings:
        if not re.search(
            rf"^##+\s+{re.escape(heading)}\s*$", body, re.MULTILINE
        ):
            add_finding(
                findings,
                "document.section",
                f"Missing required section: {heading}",
                rel,
            )

def validate_object(
    repo: Path, path: Path, expected_type: str, findings: list[Finding]
) -> None:
    rel = relative(repo, path)
    filename = OBJECT_FILE_RE.fullmatch(path.name)
    expected_prefix = "prp" if expected_type == "proposal" else "bug"
    if not filename or not filename.group(1).startswith(f"{expected_prefix}-"):
        add_finding(
            findings,
            "object.filename",
            f"Invalid {expected_type} filename",
            rel,
        )
        return
    expected_id = filename.group(1)
    slug = filename.group(2)
    if is_object_id_slug(slug):
        add_finding(
            findings,
            "object.slug_id",
            "Object filename slug must not match an object ID",
            rel,
        )
    try:
        metadata, body = read_frontmatter(path)
    except (OSError, MDFError) as exc:
        add_finding(findings, "object.frontmatter", str(exc), rel)
        return
    if metadata.get("id") != expected_id:
        add_finding(findings, "object.id", f"id must equal {expected_id}", rel)
    if metadata.get("type") != expected_type:
        add_finding(
            findings, "object.type", f"type must equal {expected_type}", rel
        )
    status = metadata.get("status")
    if expected_type == "proposal":
        # HTML 由 review 定稿时生成，不按当前状态追溯已有 PRP 的格式。
        if status == "draft" and path.suffix != ".md":
            add_finding(findings, "proposal.format", "draft PRP 必须使用 .md", rel)
    elif path.suffix != ".md":
        add_finding(findings, "object.filename", "Bug 必须使用 Markdown", rel)
    allowed_statuses = (
        {"draft", "ready", "implemented", "released", "rejected", "replaced"}
        if expected_type == "proposal"
        else BUG_STATUSES
    )
    if status not in allowed_statuses:
        add_finding(
            findings,
            "object.status",
            (
                "Proposal 状态必须符合当前交付生命周期"
                if expected_type == "proposal"
                else "Bug status must be open, fixed, closed, or rejected"
            ),
            rel,
        )
    if expected_type == "proposal":
        depends_on = metadata.get("depends_on")
        if not isinstance(depends_on, list):
            add_finding(
                findings,
                "object.depends_on",
                "Proposal depends_on must be a list of Proposal IDs or "
                "milestone names",
                rel,
            )
        elif len(depends_on) != len(set(map(str, depends_on))):
            add_finding(
                findings,
                "object.depends_on_duplicate",
                "Proposal dependencies must not contain duplicate IDs",
                rel,
            )
    elif "depends_on" in metadata:
        add_finding(
            findings,
            "bug.depends_on_forbidden",
            "Bug must not declare Proposal depends_on",
            rel,
        )
    if MARKER_RE.search(body):
        add_finding(
            findings,
            "object.marker",
            "Object contains an unresolved template marker",
            rel,
        )
    required_headings = (
        ("问题", "期望结果", "范围", "验收标准")
        if expected_type == "proposal"
        else (
            "观察到的行为",
            "期望行为",
            "复现步骤",
            "影响",
            "所需回归证据",
        )
    )
    for heading in required_headings:
        match = re.search(
            rf"^##+\s+{re.escape(heading)}\s*$", body, re.MULTILINE
        )
        if not match:
            add_finding(
                findings,
                "object.section",
                f"Missing required section: {heading}",
                rel,
            )
            continue
        next_heading = re.search(
            r"^#{1,2}\s+\S.*$", body[match.end() :], re.MULTILINE
        )
        section_end = (
            match.end() + next_heading.start() if next_heading else len(body)
        )
        if not body[match.end() : section_end].strip():
            add_finding(
                findings,
                "object.section_empty",
                f"Required section is empty: {heading}",
                rel,
            )
    if expected_type == "proposal":
        scope_match = re.search(r"^##+\s+范围\s*$", body, re.MULTILINE)
        if scope_match:
            next_heading = re.search(
                r"^#{1,2}\s+\S.*$", body[scope_match.end() :], re.MULTILINE
            )
            scope_end = (
                scope_match.end() + next_heading.start()
                if next_heading
                else len(body)
            )
            scope_body = body[scope_match.end() : scope_end]
            for subsection in ("包含", "不包含"):
                subsection_match = re.search(
                    rf"^###+\s+{subsection}\s*$", scope_body, re.MULTILINE
                )
                if not subsection_match:
                    add_finding(
                        findings,
                        "proposal.scope",
                        f"范围必须包含“{subsection}”子节",
                        rel,
                    )
                    continue
                next_subsection = re.search(
                    r"^###+\s+\S.*$",
                    scope_body[subsection_match.end() :],
                    re.MULTILINE,
                )
                subsection_end = (
                    subsection_match.end() + next_subsection.start()
                    if next_subsection
                    else len(scope_body)
                )
                if not scope_body[
                    subsection_match.end() : subsection_end
                ].strip():
                    add_finding(
                        findings,
                        "proposal.scope_empty",
                        f"范围的“{subsection}”子节不能为空",
                        rel,
                    )
    resolution = metadata.get("resolution")
    rel_parts = Path(rel).parts
    rel_parts = rel_parts[1:] if rel_parts[0] == "docs" else ()
    expected_root = "proposals" if expected_type == "proposal" else "bugs"
    if len(rel_parts) == 2 and rel_parts[0] == expected_root:
        pass
    elif (
        len(rel_parts) == 4
        and rel_parts[0] == expected_root
        and rel_parts[1] == "archive"
    ):
        if not EPOCH_RE.fullmatch(rel_parts[2]):
            add_finding(
                findings,
                "archive.path",
                "Archive slice must be MAJOR.MINOR",
                rel,
            )
        if status not in (
            {"released", "rejected", "replaced"}
            if expected_type == "proposal" else {"closed", "rejected"}
        ):
            add_finding(
                findings,
                "archive.status",
                "仅终态 Proposal 与 closed/rejected Bug 可归档",
                rel,
            )
    else:
        add_finding(
            findings,
            "object.path",
            f"{expected_type} must be directly active or in "
            "archive/MAJOR.MINOR",
            rel,
        )
    if expected_type == "proposal":
        from mdf_core.documents.proposal_schema import validate_proposal_fields
        validate_proposal_fields(metadata, rel, findings)
    else:
        if resolution is not None:
            add_finding(
                findings,
                "bug.resolution",
                "Bug must use status and reject-reason instead of resolution",
                rel,
            )
        severity = metadata.get("severity")
        if severity is not None and severity not in BUG_SEVERITIES:
            add_finding(
                findings,
                "bug.severity",
                "severity 必须是 critical、major 或 trivial",
                rel,
            )
        if status in {"open", "fixed", "closed"} and severity not in BUG_SEVERITIES:
            add_finding(
                findings,
                "bug.severity_required",
                "非 duplicate 的 active Bug 必须有 severity",
                rel,
            )
        reject_reason = metadata.get("reject-reason")
        duplicate_of = metadata.get("duplicate_of")
        if status == "rejected":
            if reject_reason not in BUG_REJECT_REASONS:
                add_finding(
                    findings,
                    "bug.reject_reason",
                    "rejected Bug requires a supported reject-reason",
                    rel,
                )
        elif reject_reason is not None:
            add_finding(
                findings,
                "bug.reject_reason",
                "reject-reason is allowed only with status rejected",
                rel,
            )
        if status == "rejected" and reject_reason == "duplicate":
            if not isinstance(duplicate_of, str) or not duplicate_of.startswith(
                "bug-"
            ):
                add_finding(
                    findings,
                    "bug.duplicate_of",
                    "duplicate Bug 需要 duplicate_of: bug-...",
                    rel,
                )
            for key in ("found_in", "fixed_in"):
                if key in metadata:
                    add_finding(
                        findings,
                        "bug.duplicate_version",
                        "duplicate Bug 不使用 found_in 或 fixed_in",
                        rel,
                    )
        else:
            if duplicate_of is not None:
                add_finding(
                    findings,
                    "bug.duplicate_of",
                    "duplicate_of 仅允许用于 rejected duplicate Bug",
                    rel,
                )
            found_in = metadata.get("found_in")
            if (
                not is_unreleased_sentinel(found_in)
                and stable_semver(found_in) is None
            ):
                add_finding(
                    findings,
                    "bug.found_in",
                    "found_in 必须是稳定 SemVer 或 unreleased",
                    rel,
                )
            fixed_in = metadata.get("fixed_in")
            if status == "closed" and stable_semver(fixed_in) is None:
                add_finding(
                    findings,
                    "bug.fixed_in",
                    "A fixed Bug needs a stable SemVer fixed_in",
                    rel,
                )
            if fixed_in is not None and stable_semver(fixed_in) is None:
                add_finding(
                    findings,
                    "bug.version",
                    "fixed_in must be a stable SemVer",
                    rel,
                )
            if status != "closed" and fixed_in is not None:
                add_finding(
                    findings,
                    "bug.fixed_in",
                    "fixed_in is allowed only with status closed",
                    rel,
                )
    sentinel_metadata = dict(metadata)
    if expected_type == "bug" and is_unreleased_sentinel(
        metadata.get("found_in")
    ):
        sentinel_metadata.pop("found_in", None)
    if contains_unreleased_sentinel(sentinel_metadata):
        add_finding(
            findings,
            "version.sentinel_scope",
            "unreleased 仅允许出现在 Bug found_in",
            rel,
        )
