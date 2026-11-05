from pathlib import Path
from typing import Any

from mdf_core.documents.archive import archive_plan
from mdf_core.lifecycle.closeout_render import (
    merge_evidence,
    render_version_change,
    update_changelog_text,
    update_manifest_release,
)
from mdf_core.foundation.constants import CHANGELOG_CATEGORIES, OBJECT_FILE_RE, is_unreleased_sentinel
from mdf_core.foundation.errors import MDFError
from mdf_core.documents.moves import (
    managed_delivery_markdown,
    apply_moves_and_rewrites,
    moved_destination,
    opaque_links_survive_move,
    replacement_plan,
)
from mdf_core.foundation.paths import manifest_path, relative
from mdf_core.foundation.semver import bump_kind, required_bump
from mdf_core.foundation.yamlutil import read_frontmatter


def apply_version_closeout(
    repo: Path,
    context: dict[str, Any],
    *,
    all_slugs: list[str],
    notes: dict[str, list[str]],
    breaking: bool,
    evidence: dict[str, list[str]],
    proposal_ids: set[str],
    fixed_ids: set[str],
    closed_ids: set[str],
    deferred_ids: set[str],
    adrs: set[str],
    closed_proposal_resolutions: dict[str, str],
    objects: dict[str, tuple[str, Path, dict[str, Any]]],
    closures: list[dict[str, Any]],
    hotfix_body: str | None,
) -> dict[str, Any]:
    categories = {
        category for category in CHANGELOG_CATEGORIES if notes[category]
    }
    actual_bump = bump_kind(context["previous_tuple"], context["candidate"])
    minimum_bump = required_bump(
        context["previous_tuple"],
        categories or {"none"},
        breaking,
    )
    rank = {"patch": 1, "minor": 2, "major": 3}
    if rank[actual_bump] < rank[minimum_bump]:
        raise MDFError(
            (
                f"Release uses a {actual_bump} bump but the Change set "
                f"requires at least {minimum_bump}"
            ),
            code="insufficient_bump",
        )

    release_dir = repo / "changes" / context["version"]
    moves: dict[Path, Path] = {}
    move_records: list[dict[str, Any]] = []
    for item in context["release_items"]:
        source = repo / item["source"]
        destination = release_dir / item["slug"]
        broken = opaque_links_survive_move(repo, source, destination)
        if broken:
            raise MDFError(
                "Moving the Change would break an opaque Markdown link",
                code="opaque_link_would_break",
                details={"links": broken},
            )
        moves[source] = destination
        move_records.append(
            {
                "kind": "repo",
                "from": item["source"],
                "to": relative(repo, destination),
            }
        )
    review_source = repo / "changes" / "unreleased" / context["version"]
    if review_source.is_dir() and not review_source.is_symlink():
        for path in sorted(review_source.iterdir()):
            if not path.is_file() or path.is_symlink():
                continue
            destination = release_dir / path.name
            moves[path] = destination
            move_records.append(
                {
                    "kind": "repo",
                    "from": relative(repo, path),
                    "to": relative(repo, destination),
                }
            )
    epoch = ".".join(context["version"].split(".")[:2])
    archive_moves, _ = archive_plan(repo, epoch)
    archived: list[tuple[str, str]] = []
    for source, destination in archive_moves.items():
        metadata, _ = read_frontmatter(source)
        identifier = metadata.get("id")
        if isinstance(identifier, str):
            archived.append((identifier, relative(repo, destination)))
        moves[source] = destination
        move_records.append(
            {
                "kind": "repo",
                "from": relative(repo, source),
                "to": relative(repo, destination),
            }
        )
    rewrites = replacement_plan(
        repo,
        moves,
        rewrite_inside_sources=False,
        rewrite_inside_filter=lambda path: (
            path.name == "CHANGE.md" or managed_delivery_markdown(path)
            or (
                path.relative_to(repo).parts[:2] in {("docs", "proposals"), ("docs", "bugs")}
                and OBJECT_FILE_RE.fullmatch(path.name) is not None
            )
        ),
    )
    apply_moves_and_rewrites(moves, rewrites)
    if review_source.is_dir() and not any(review_source.iterdir()):
        review_source.rmdir()

    release_dir.mkdir(parents=True, exist_ok=True)
    found_in_transitions: list[str] = []
    for closure in closures:
        identifier = closure["id"]
        if not identifier.startswith("bug-"):
            continue
        record = objects.get(identifier)
        if record is not None and is_unreleased_sentinel(
            record[2].get("found_in")
        ):
            found_in_transitions.append(
                f"{identifier}: unreleased -> {context['version']}"
            )
    validation_commands = context["validation_commands"]
    root_evidence = merge_evidence(
        evidence,
        {"commands": validation_commands},
    )
    release_path = release_dir / "CHANGE.md"
    release_path.write_text(
        render_version_change(
            context["version"],
            context["previous"],
            context["release_date"],
            context["mode"],
            all_slugs,
            categories,
            breaking,
            minimum_bump,
            actual_bump,
            validation_commands,
            proposal_ids,
            fixed_ids,
            closed_ids,
            deferred_ids,
            adrs,
            closed_proposal_resolutions,
            found_in_transitions,
            context.get("deferred_acceptance", {}),
            hotfix_body,
            release_notes=notes,
            evidence=root_evidence,
            verify_command_results=context.get("verify_command_results") or [],
        ),
        encoding="utf-8",
    )
    changelog_path = repo / "CHANGELOG.md"
    changelog_path.write_text(
        update_changelog_text(
            changelog_path.read_text(encoding="utf-8"),
            version=context["version"],
            release_date=context["release_date"],
            notes=notes,
        ),
        encoding="utf-8",
    )
    manifest = manifest_path(repo)
    manifest.write_text(
        update_manifest_release(
            manifest.read_text(encoding="utf-8"),
            context["version"],
        ),
        encoding="utf-8",
    )
    return {
        "slugs": sorted(all_slugs),
        "moves": sorted(move_records, key=lambda item: item["to"]),
        "archived": [
            {"id": identifier, "path": path}
            for identifier, path in sorted(archived)
        ],
        "semver": {
            "categories": sorted(categories),
            "breaking": breaking,
            "required_bump": minimum_bump,
            "actual_bump": actual_bump,
        },
        "rewrites": [
            relative(repo, moved_destination(path, moves))
            for path in sorted(rewrites)
        ],
        "outcomes": {
            "proposals": sorted(proposal_ids),
            "fixed": sorted(fixed_ids),
            "closed": sorted(closed_ids),
            "deferred": sorted(deferred_ids),
            "closed_proposals": closed_proposal_resolutions,
        },
    }
