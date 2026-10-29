import datetime as dt
from pathlib import Path
from typing import Any

from mdf_core.lifecycle.closeout_validate import CLOSURE_RESOLUTIONS, require_exact_keys, require_spec_key
from mdf_core.foundation.constants import SCHEMA_VERSION
from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import current_branch
from mdf_core.foundation.paths import load_manifest, relative
from mdf_core.foundation.textutil import stable_semver


def unreleased_change_slugs(repo: Path, version: str) -> list[str]:
    unreleased = repo / "changes" / "unreleased"
    if not unreleased.is_dir():
        return []
    names = sorted(
        path.name
        for path in unreleased.iterdir()
        if path.is_dir() and not path.is_symlink()
    )
    unexpected = [
        name for name in names
        if stable_semver(name) is not None and name != version
    ]
    if unexpected:
        raise MDFError(
            "unreleased 中的 SemVer 目录必须等于当前收口版本",
            code="unexpected_review_dir",
            details={"unexpected": unexpected, "version": version},
        )
    return [name for name in names if stable_semver(name) is None]


def validate_closeout_shape(
    repo: Path,
    spec: dict[str, Any],
) -> dict[str, Any]:
    if (
        type(spec.get("schema_version")) is not int
        or spec.get("schema_version") != SCHEMA_VERSION
    ):
        raise MDFError(
            f"closeout payload 的 schema_version 必须为 {SCHEMA_VERSION}",
            code="invalid_closeout_spec",
        )
    mode = require_spec_key(spec, "mode")
    if mode not in {"release", "hotfix"}:
        raise MDFError(
            "closeout mode 必须是 release 或 hotfix",
            code="invalid_closeout_spec",
        )
    version = require_spec_key(spec, "version")
    candidate = stable_semver(version)
    if candidate is None:
        raise MDFError(
            "closeout version 必须是稳定 SemVer",
            code="invalid_closeout_spec",
        )
    expected_branch = f"{mode}/{version}"
    if spec.get("expected_branch") != expected_branch:
        raise MDFError(
            f"expected_branch must equal {expected_branch}",
            code="invalid_closeout_spec",
        )
    actual_branch = current_branch(repo)
    if actual_branch != expected_branch:
        raise MDFError(
            f"Current branch is {actual_branch}; expected {expected_branch}",
            code="branch_mismatch",
        )
    release_date_raw = require_spec_key(spec, "release_date")
    try:
        release_date = dt.date.fromisoformat(release_date_raw)
    except (TypeError, ValueError) as exc:
        raise MDFError(
            "release_date 必须使用 YYYY-MM-DD",
            code="invalid_closeout_spec",
        ) from exc
    if release_date.isoformat() != release_date_raw:
        raise MDFError(
            "release_date 必须使用规范 YYYY-MM-DD",
            code="invalid_closeout_spec",
        )

    manifest = load_manifest(repo)
    versioning = manifest.get("versioning")
    manifest_previous = (
        versioning.get("latest_release")
        if isinstance(versioning, dict)
        else None
    )
    previous = require_spec_key(spec, "previous_version")
    if previous is not None and stable_semver(previous) is None:
        raise MDFError(
            "previous_version 必须为 null 或稳定 SemVer",
            code="invalid_closeout_spec",
        )
    if previous != manifest_previous:
        raise MDFError(
            "previous_version 与 manifest latest_release 不一致",
            code="release_history_mismatch",
            details={"manifest": manifest_previous, "spec": previous},
        )
    previous_tuple = (0, 0, 0) if previous is None else stable_semver(previous)
    if previous_tuple is None or candidate <= previous_tuple:
        raise MDFError(
            "closeout version 必须大于 previous_version",
            code="not_increasing",
        )
    target = repo / "changes" / version
    if target.exists():
        raise MDFError(
            f"Release directory already exists: {relative(repo, target)}",
            code="collision",
        )

    actual_slugs = unreleased_change_slugs(repo, version)
    release_items = [
        {"slug": slug, "source": f"changes/unreleased/{slug}"}
        for slug in actual_slugs
    ]
    slugs = actual_slugs
    if mode == "release":
        if not slugs:
            raise MDFError(
                "release 模式至少需要一个 unreleased feature/bugfix/adhoc Change",
                code="invalid_closeout_spec",
            )
    else:
        if slugs:
            raise MDFError(
                "hotfix 分支跳过 unreleased Change；closeout 前须清空 unreleased",
                code="hotfix_unreleased_present",
            )

    raw_closures = require_spec_key(spec, "closures")
    if not isinstance(raw_closures, list):
        raise MDFError(
            "closures must be a list",
            code="invalid_closeout_spec",
        )
    closures: list[dict[str, Any]] = []
    closure_ids: set[str] = set()
    for index, raw_closure in enumerate(raw_closures):
        closure = require_exact_keys(
            raw_closure,
            {"id", "resolution"},
            {"released_in", "fixed_in"},
            f"closures[{index}]",
        )
        identifier = closure["id"]
        if not isinstance(identifier, str) or identifier in closure_ids:
            raise MDFError(
                "closure IDs must be unique strings",
                code="invalid_closeout_spec",
            )
        resolution = closure["resolution"]
        if (
            not isinstance(resolution, str)
            or resolution not in CLOSURE_RESOLUTIONS
        ):
            raise MDFError(
                f"closures[{index}].resolution 必须是受支持的 resolution",
                code="invalid_closeout_spec",
                details={
                    "id": identifier,
                    "resolution": resolution,
                    "allowed": sorted(CLOSURE_RESOLUTIONS),
                },
            )
        closure_ids.add(identifier)
        closures.append(dict(closure))
    validation_commands = require_spec_key(spec, "validation_commands")
    if (
        not isinstance(validation_commands, list)
        or not validation_commands
        or any(
            not isinstance(command, str) or not command.strip()
            for command in validation_commands
        )
    ):
        raise MDFError(
            "validation_commands 必须是非空字符串列表",
            code="invalid_closeout_spec",
        )
    return {
        "mode": mode,
        "version": version,
        "candidate": candidate,
        "previous": previous,
        "previous_tuple": previous_tuple,
        "release_date": release_date.isoformat(),
        "release_items": release_items,
        "hotfix": None,
        "hotfix_change": spec.get("hotfix_change"),
        "closures": closures,
        "validation_commands": list(validation_commands),
        "deferred_acceptance": spec.get("deferred_acceptance", {}),
        "verify_command_results": spec.get("verify_command_results") or [],
    }
