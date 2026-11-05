"""Bug 身份与 bugfix 开工判定。"""
from pathlib import Path

from mdf_core.foundation.constants import OBJECT_FILE_RE, OBJECT_ID_RE
from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import run
from mdf_core.inspection.validate_objects import iter_object_files
from mdf_core.foundation.yamlutil import read_frontmatter


def bug_id_on_ref(repo, identifier, ref):
    if (
        not isinstance(identifier, str)
        or not identifier.startswith("bug-")
        or OBJECT_ID_RE.fullmatch(identifier) is None
    ):
        raise MDFError("bugfix 需要 Bug ID", code="missing_bug")
    listed = run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", "docs/bugs"],
        cwd=repo,
    )
    found = []
    for rel in listed.stdout.splitlines():
        parts = Path(rel).parts
        if len(parts) != 3 or parts[:2] != ("docs", "bugs"):
            continue
        match = OBJECT_FILE_RE.fullmatch(parts[2])
        if match and match.group(1) == identifier:
            found.append(match.group(1))
    if not found:
        raise MDFError("缺少指定 Bug", code="missing_bug")
    if len(found) > 1:
        raise MDFError("Bug ID 重复", code="invalid_bugs")
    return found[0]


def require_startable_bug(repo, identifier):
    from mdf_core.foundation.paths import load_manifest
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("start 需要 ready 仓库", code="manifest_not_ready")
    found = None
    for path in iter_object_files(repo, "bug"):
        if len(path.relative_to(repo / "docs").parts) != 2:
            continue
        meta, _ = read_frontmatter(path)
        if meta.get("id") == identifier:
            found = (path, meta)
            break
    if found is None:
        raise MDFError("缺少指定 Bug", code="missing_bug")
    path, meta = found
    if meta.get("status") != "open":
        raise MDFError("bugfix 需要 active open Bug", code="bug_not_open")
    return path
