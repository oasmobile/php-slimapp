from pathlib import Path

from mdf_core.foundation.constants import EPOCH_RE
from mdf_core.foundation.errors import MDFError
from mdf_core.documents.moves import replacement_plan
from mdf_core.foundation.paths import relative
from mdf_core.inspection.validate_objects import iter_object_files
from mdf_core.foundation.yamlutil import read_frontmatter


def archive_plan(
    repo: Path, epoch: str
) -> tuple[dict[Path, Path], dict[Path, str]]:
    if not EPOCH_RE.fullmatch(epoch):
        raise MDFError("Archive epoch must be MAJOR.MINOR", code="bad_epoch")
    moves: dict[Path, Path] = {}
    records: dict[str, tuple[Path, dict[str, Any]]] = {}
    for kind, directory in (("proposal", "docs/proposals"), ("bug", "docs/bugs")):
        for path in iter_object_files(repo, kind):
            records_path_parts = path.relative_to(repo / "docs").parts
            try:
                metadata, _ = read_frontmatter(path)
            except MDFError as exc:
                raise MDFError(
                    "Cannot archive invalid object "
                    f"{relative(repo, path)}: {exc}",
                    code="invalid_object",
                ) from exc
            identifier = metadata.get("id")
            if isinstance(identifier, str):
                records[identifier] = (path, metadata)
            if len(records_path_parts) != 2:
                continue
            allowed_statuses = (
                {"released", "replaced", "rejected"}
                if kind == "proposal" else {"closed", "rejected"}
            )
            if metadata.get("status") not in allowed_statuses:
                continue
            root = repo / directory
            target = root / "archive" / epoch / path.name
            if target.exists():
                raise MDFError(
                    "Archive destination already exists: "
                    f"{relative(repo, target)}",
                    code="collision",
                )
            moves[path] = target
    # A duplicate is an archive-group member, never an independent record.
    # The canonical Bug must already be closed; otherwise closeout/audit must
    # stop instead of silently splitting the group across archive epochs.
    for path, metadata in list(records.values()):
        if (
            metadata.get("type") != "bug"
            or metadata.get("status") != "rejected"
            or metadata.get("reject-reason") != "duplicate"
        ):
            continue
        primary_id = metadata.get("duplicate_of")
        primary = (
            records.get(primary_id) if isinstance(primary_id, str) else None
        )
        if primary is None:
            continue
        primary_path, primary_metadata = primary
        if primary_metadata.get("status") not in {"closed", "rejected"}:
            raise MDFError(
                "Duplicate archive group is not closed: "
                f"{relative(repo, primary_path)}",
                code="duplicate_group_open",
            )
        primary_parts = primary_path.relative_to(repo / "docs").parts
        group_epoch = (
            primary_parts[2]
            if len(primary_parts) == 4 and primary_parts[1] == "archive"
            else epoch
        )
        if len(primary_parts) == 2:
            target = repo / "docs/bugs" / "archive" / group_epoch / primary_path.name
            if target.exists() and primary_path not in moves:
                raise MDFError(
                    "Archive destination already exists: "
                    f"{relative(repo, target)}",
                    code="collision",
                )
            moves.setdefault(primary_path, target)
        if len(path.relative_to(repo / "docs").parts) == 2:
            target = repo / "docs/bugs" / "archive" / group_epoch / path.name
            if target.exists() and path not in moves:
                raise MDFError(
                    "Archive destination already exists: "
                    f"{relative(repo, target)}",
                    code="collision",
                )
            moves[path] = target
    rewrites = replacement_plan(repo, moves)
    return moves, rewrites
