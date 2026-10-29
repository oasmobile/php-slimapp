from pathlib import Path
from typing import Any

from mdf_core.lifecycle.closeout_objects import active_objects
from mdf_core.foundation.errors import Finding, MDFError, add_finding, serialize_findings
from mdf_core.foundation.paths import relative
from mdf_core.inspection.validate_change_schema import validate_change_file
from mdf_core.inspection.validate_links import validate_links
from mdf_core.inspection.validate_records import validate_record_references
from mdf_core.execution.verification import required_suites


def summarize_closeout(repo: Path, context: dict[str, Any]) -> dict[str, Any]:
    """Produce a read-only closeout preview without running verification."""
    all_slugs = [item["slug"] for item in context["release_items"]]
    findings: list[Finding] = []
    for slug in all_slugs:
        path = repo / "changes" / "unreleased" / slug / "CHANGE.md"
        if not path.is_file():
            add_finding(
                findings,
                "change.missing",
                "Release-set directory requires CHANGE.md",
                f"changes/unreleased/{slug}",
            )
        else:
            validate_change_file(repo, path, findings, expected_slug=slug)
    validate_record_references(repo, findings)
    validate_links(repo, findings)
    if findings:
        raise MDFError(
            "Release set is invalid",
            code="invalid_release_set",
            details={"findings": serialize_findings(findings)},
        )

    moves = [
        {
            "from": item["source"],
            "to": f"changes/{context['version']}/{item['slug']}",
        }
        for item in context["release_items"]
    ]
    epoch = ".".join(context["version"].split(".")[:2])
    active = active_objects(repo)
    for closure in context["closures"]:
        if closure["resolution"] == "deferred":
            continue
        identifier = closure["id"]
        record = active.get(identifier)
        if record is None:
            continue
        kind, path, _metadata = record
        root = "docs/proposals" if kind == "proposal" else "docs/bugs"
        target = f"{root}/archive/{epoch}/{path.name}"
        moves.append({"from": relative(repo, path), "to": target})
    affected = {
        ".mdf/manifest.yaml",
        "CHANGELOG.md",
        f"changes/{context['version']}/CHANGE.md",
        *(item["from"] for item in moves),
        *(item["to"] for item in moves),
    }
    return {
        "version": context["version"],
        "outcomes": [
            {"id": closure["id"], "resolution": closure["resolution"]}
            for closure in context["closures"]
        ],
        "moves": moves,
        "affected_files": sorted(affected),
        "verification": {
            "suites": required_suites(context["mode"]),
            "commands": context["validation_commands"],
            "executed": False,
        },
    }
