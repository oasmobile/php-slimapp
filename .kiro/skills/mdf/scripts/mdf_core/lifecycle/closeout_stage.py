from pathlib import Path
from typing import Any

from mdf_core.lifecycle.closeout_commit import apply_version_closeout
from mdf_core.lifecycle.closeout_objects import active_objects, close_object_text
from mdf_core.lifecycle.closeout_render import aggregate_release_changes
from mdf_core.foundation.constants import (
    BUG_SEVERITIES,
    BUG_TERMINAL_RESOLUTIONS,
    CHANGELOG_CATEGORIES,
    PROPOSAL_CLOSED_RESOLUTIONS,
    is_unreleased_sentinel,
)
from mdf_core.foundation.errors import Finding, MDFError, add_finding, serialize_findings
from mdf_core.lifecycle.closeout_summary import summarize_closeout
from mdf_core.inspection.validate_change_schema import validate_change_file
from mdf_core.inspection.validate_links import validate_links
from mdf_core.inspection.validate_records import validate_record_references
from mdf_core.foundation.yamlutil import read_frontmatter


def apply_closeout(
    repo: Path,
    context: dict[str, Any],
) -> dict[str, Any]:
    all_slugs = [item["slug"] for item in context["release_items"]]
    change_findings: list[Finding] = []
    for slug in all_slugs:
        change_path = repo / "changes" / "unreleased" / slug / "CHANGE.md"
        if not change_path.is_file():
            add_finding(
                change_findings,
                "change.missing",
                "Release-set directory requires CHANGE.md",
                f"changes/unreleased/{slug}",
            )
            continue
        validate_change_file(
            repo,
            change_path,
            change_findings,
            expected_slug=slug,
        )
    validate_record_references(repo, change_findings)
    validate_links(repo, change_findings)
    if change_findings:
        raise MDFError(
            "Release set is invalid",
            code="invalid_release_set",
            details={"findings": serialize_findings(change_findings)},
        )

    if context["mode"] == "hotfix":
        hotfix_change = context.get("hotfix_change") or {}
        if not isinstance(hotfix_change, dict):
            raise MDFError(
                "hotfix_change 必须是内存对象", code="invalid_closeout_spec"
            )
        notes = {category: [] for category in CHANGELOG_CATEGORIES}
        raw_notes = hotfix_change.get("release_notes")
        if isinstance(raw_notes, dict):
            for category in CHANGELOG_CATEGORIES:
                values = raw_notes.get(category, [])
                if isinstance(values, list):
                    notes[category] = [str(value) for value in values]
        evidence = dict(hotfix_change.get("evidence", {}))
        breaking = hotfix_change.get("breaking") is True
        proposal_ids = set(hotfix_change.get("proposals", []))
        fixed_ids = set(hotfix_change.get("fixed", []))
        closed_ids = set(hotfix_change.get("closed", []))
        deferred_ids = set(hotfix_change.get("deferred", []))
        adrs = set(hotfix_change.get("adrs", []))
        hotfix_body = (
            hotfix_change.get("body")
            if isinstance(hotfix_change.get("body"), str)
            else "Hotfix result verified."
        )
    else:
        (
            notes,
            breaking,
            proposal_ids,
            fixed_ids,
            closed_ids,
            deferred_ids,
            adrs,
            evidence,
        ) = aggregate_release_changes(repo, all_slugs)
        hotfix_body = None
    if (
        fixed_ids & closed_ids
        or fixed_ids & deferred_ids
        or closed_ids & deferred_ids
    ):
        raise MDFError(
            "每个 Bug 只能出现在 fixed、closed、deferred 之一",
            code="change_outcome_overlap",
        )
    bug_ids = fixed_ids | closed_ids | deferred_ids
    baseline_closures = proposal_ids | bug_ids
    closures = context["closures"]
    closure_ids = {closure["id"] for closure in closures}
    if not baseline_closures.issubset(closure_ids):
        raise MDFError(
            "closures 必须覆盖 Change 声明的全部 Proposal 与 Bug outcome",
            code="closure_set_mismatch",
            details={
                "expected_minimum": sorted(baseline_closures),
                "specified": sorted(closure_ids),
                "missing": sorted(baseline_closures - closure_ids),
            },
        )
    objects = active_objects(repo)
    closed_proposal_resolutions: dict[str, str] = {}
    for closure in closures:
        resolution = closure["resolution"]
        identifier = closure["id"]
        if identifier in proposal_ids and resolution != "released":
            raise MDFError(
                f"Proposal closeout must use released: {identifier}",
                code="invalid_closure",
            )
        if identifier in fixed_ids and resolution != "fixed":
            raise MDFError(
                f"Fixed Bug must use fixed resolution: {identifier}",
                code="invalid_closure",
            )
        if identifier in deferred_ids and resolution != "deferred":
            raise MDFError(
                f"Deferred Bug must use deferred outcome: {identifier}",
                code="invalid_closure",
            )
        if (
            identifier in closed_ids
            and resolution not in BUG_TERMINAL_RESOLUTIONS
        ):
            raise MDFError(
                "Closed Bug must use a terminal non-fixed resolution: "
                f"{identifier}",
                code="invalid_closure",
            )
        if identifier not in baseline_closures:
            record = objects.get(identifier)
            object_kind = record[0] if record is not None else None
            if resolution == "fixed":
                fixed_ids.add(identifier)
            elif resolution == "deferred":
                deferred_ids.add(identifier)
            elif resolution == "released":
                proposal_ids.add(identifier)
            elif (
                resolution in PROPOSAL_CLOSED_RESOLUTIONS
                and object_kind == "proposal"
            ):
                closed_proposal_resolutions[identifier] = resolution
            elif (
                resolution in BUG_TERMINAL_RESOLUTIONS
                and object_kind != "proposal"
            ):
                closed_ids.add(identifier)
            else:
                raise MDFError(
                    "Supplemental closure has unsupported resolution: "
                    f"{identifier}",
                    code="invalid_closure",
                )
    unreleased_active = sorted(
        identifier
        for identifier, (kind, _path, metadata) in objects.items()
        if kind == "bug"
        and metadata.get("status") in {"open", "fixed", "closed", "rejected"}
        and is_unreleased_sentinel(metadata.get("found_in"))
        and metadata.get("reject-reason") != "duplicate"
    )
    classified_bugs = {
        closure["id"]
        for closure in closures
        if closure["id"].startswith("bug-")
    }
    missing_unreleased = [
        identifier
        for identifier in unreleased_active
        if identifier not in classified_bugs
    ]
    if missing_unreleased:
        raise MDFError(
            "每个 active 且 found_in: unreleased 的 Bug 必须出现在 closeout outcomes 中",
            code="unclassified_unreleased_bug",
            details={"missing": missing_unreleased},
        )
    for closure in closures:
        resolution = closure["resolution"]
        identifier = closure["id"]
        record = objects.get(identifier)
        if record is None:
            raise MDFError(
                "Closure object is not an active canonical object: "
                f"{identifier}",
                code="invalid_closure",
            )
        kind, path, metadata = record
        expected_kind = (
            "proposal"
            if identifier in proposal_ids
            or identifier in closed_proposal_resolutions
            else "bug"
        )
        expected_status = (
            ("implemented" if resolution == "released" else "rejected")
            if kind == "proposal"
            else (
                "closed"
                if resolution == "fixed"
                else "open" if resolution == "deferred" else "rejected"
            )
        )
        if kind != expected_kind or metadata.get("status") != expected_status:
            raise MDFError(
                f"Closure object has the wrong type or state: {identifier}",
                code="invalid_closure",
            )
        if (
            kind == "bug"
            and metadata.get("status") == "rejected"
            and metadata.get("reject-reason") == "duplicate"
        ):
            raise MDFError(
                "duplicate Bug 不得进入 Change outcomes；请改用 canonical Bug ID",
                code="duplicate_in_changeset",
            )
        if kind == "bug":
            severity = metadata.get("severity")
            resolution = closure["resolution"]
            if (
                resolution == "deferred"
                or resolution in BUG_TERMINAL_RESOLUTIONS
            ) and severity == "critical":
                raise MDFError(
                    f"critical Bug 只能 fixed: {identifier}",
                    code="critical_bug_blocks_release",
                )
            if resolution == "deferred" and severity not in BUG_SEVERITIES:
                raise MDFError(
                    f"Deferred Bug has no valid severity: {identifier}",
                    code="invalid_closure",
                )
            if resolution in {"deferred", "wont-fix"} and severity == "major":
                acceptance = context.get("deferred_acceptance", {})
                item = (
                    acceptance.get(identifier)
                    if isinstance(acceptance, dict)
                    else None
                )
                if (
                    not isinstance(item, dict)
                    or not item.get("accepted")
                    or not str(item.get("reason", "")).strip()
                    or not str(item.get("follow_up", "")).strip()
                ):
                    raise MDFError(
                        f"major Bug 需要明确接受、理由与 follow-up: {identifier}",
                        code="severity_gate",
                    )
        original = path.read_text(encoding="utf-8")
        updated = close_object_text(
            original,
            kind=kind,
            closure=closure,
            version=context["version"],
        )
        path.write_text(updated, encoding="utf-8")

    return apply_version_closeout(
        repo,
        context,
        all_slugs=all_slugs,
        notes=notes,
        breaking=breaking,
        evidence=evidence,
        proposal_ids=proposal_ids,
        fixed_ids=fixed_ids,
        closed_ids=closed_ids,
        deferred_ids=deferred_ids,
        adrs=adrs,
        closed_proposal_resolutions=closed_proposal_resolutions,
        objects=objects,
        closures=closures,
        hotfix_body=hotfix_body,
    )
