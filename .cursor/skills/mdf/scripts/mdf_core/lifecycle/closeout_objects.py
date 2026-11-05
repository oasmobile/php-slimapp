import re
from pathlib import Path
from typing import Any

from mdf_core.foundation.constants import (
    BUG_REJECT_REASONS,
    BUG_RESOLUTIONS,
    BUG_SEVERITIES,
    is_unreleased_sentinel,
)
from mdf_core.foundation.errors import MDFError
from mdf_core.inspection.validate_objects import iter_object_files
from mdf_core.foundation.yamlutil import frontmatter_span, parse_yaml


def active_objects(repo: Path) -> dict[str, tuple[str, Path, dict[str, Any]]]:
    result: dict[str, tuple[str, Path, dict[str, Any]]] = {}
    for kind in ("proposal", "bug"):
        for path in iter_object_files(repo, kind):
            if len(path.relative_to(repo / "docs").parts) != 2:
                continue
            text = path.read_text(encoding="utf-8")
            start, end, _ = frontmatter_span(text)
            metadata = parse_yaml(text[start:end])
            identifier = metadata.get("id")
            if isinstance(identifier, str):
                result[identifier] = (kind, path, metadata)
    return result


def _set_field(frontmatter: str, key: str, value: str) -> str:
    pattern = rf"^{re.escape(key)}:\s*.*$"
    updated, count = re.subn(
        pattern,
        f"{key}: {value}",
        frontmatter,
        count=1,
        flags=re.MULTILINE,
    )
    return updated if count else frontmatter + f"\n{key}: {value}"


def _remove_field(frontmatter: str, key: str) -> str:
    return re.sub(
        rf"^{re.escape(key)}:\s*.*\n?",
        "",
        frontmatter,
        count=1,
        flags=re.MULTILINE,
    )


def _require_status(
    metadata: dict[str, Any], identifier: str, expected: str
) -> None:
    if metadata.get("status") != expected:
        raise MDFError(
            f"Object {identifier} is not {expected}", code="invalid_closure"
        )


def close_object_text(
    text: str,
    *,
    kind: str,
    closure: dict[str, Any],
    version: str,
) -> str:
    """Close one object from parsed YAML state and normalize changed fields."""
    start, end, _ = frontmatter_span(text)
    frontmatter = text[start:end]
    metadata = parse_yaml(frontmatter)
    identifier = closure.get("id")
    resolution = closure["resolution"]

    if kind == "proposal":
        if resolution == "released":
            _require_status(metadata, str(identifier), "implemented")
            if closure.get("released_in") != version or "fixed_in" in closure:
                raise MDFError("released 需要匹配发布版本", code="invalid_closure")
            frontmatter = _set_field(frontmatter, "status", "released")
            frontmatter = _set_field(frontmatter, "released_in", version)
        else:
            _require_status(metadata, str(identifier), "rejected")
            if resolution != metadata.get("reject-reason"):
                raise MDFError("拒绝原因不一致", code="invalid_closure")
            if "released_in" in closure or "fixed_in" in closure:
                raise MDFError("拒绝结果不使用发布版本", code="invalid_closure")
        return text[:start] + frontmatter + text[end:]

    if resolution == "deferred":
        _require_status(metadata, str(identifier), "open")
        severity = metadata.get("severity")
        if severity not in BUG_SEVERITIES:
            raise MDFError(
                "Deferred Bugs require critical, major, or trivial severity",
                code="invalid_closure",
            )
        if is_unreleased_sentinel(metadata.get("found_in")):
            frontmatter = _set_field(frontmatter, "found_in", version)
        return text[:start] + frontmatter + text[end:]

    if resolution not in BUG_RESOLUTIONS:
        raise MDFError(
            f"Invalid Bug resolution: {resolution}",
            code="invalid_closure",
        )
    if resolution == "fixed":
        _require_status(metadata, str(identifier), "closed")
        if (
            metadata.get("fixed_in") != version
            or closure.get("fixed_in") != version
            or "released_in" in closure
        ):
            raise MDFError(
                "fixed closure requires fixed_in equal to release version",
                code="invalid_closure",
            )
        if is_unreleased_sentinel(metadata.get("found_in")):
            frontmatter = _set_field(frontmatter, "found_in", version)
    elif resolution in BUG_REJECT_REASONS:
        _require_status(metadata, str(identifier), "rejected")
        if metadata.get("reject-reason") != resolution:
            raise MDFError(
                "Rejected Bug closure must match reject-reason",
                code="invalid_closure",
            )
        if is_unreleased_sentinel(metadata.get("found_in")):
            frontmatter = _set_field(frontmatter, "found_in", version)
    else:
        raise MDFError(
            f"Invalid Bug resolution: {resolution}", code="invalid_closure"
        )
    return text[:start] + frontmatter + text[end:]
