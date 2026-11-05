"""bug close intent 完成验收后调用的确定性状态写入。"""
from mdf_core.lifecycle.closeout_objects import active_objects, _set_field
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import branch_details, current_branch, repo_path, require_git_root
from mdf_core.foundation.paths import ensure_safe_managed_paths, load_manifest
from mdf_core.foundation.textutil import stable_semver
from mdf_core.foundation.yamlutil import frontmatter_span


def command_bug_close(args) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_safe_managed_paths(repo)
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("bug close 需要 ready", code="manifest_not_ready")
    version = args.fixed_in
    if stable_semver(version) is None:
        raise MDFError("--fixed-in 必须是稳定 SemVer", code="invalid_fixed_in")
    details = branch_details(current_branch(repo))
    if details["kind"] in {"release", "hotfix"} and details["version"] != version:
        raise MDFError("--fixed-in 必须与分支版本一致", code="invalid_fixed_in")
    record = active_objects(repo).get(args.bug_id)
    if record is None or record[0] != "bug":
        raise MDFError("缺少指定 active Bug", code="missing_bug")
    _, path, metadata = record
    if metadata.get("status") != "fixed":
        raise MDFError("bug close 只接受 fixed Bug", code="bug_not_fixed")
    text = path.read_text(encoding="utf-8")
    start, end, _ = frontmatter_span(text)
    frontmatter = _set_field(text[start:end], "fixed_in", version)
    frontmatter = _set_field(frontmatter, "status", "closed")
    path.write_text(text[:start] + frontmatter + text[end:], encoding="utf-8")
    emit({"ok": True, "operation": "bug-close", "id": args.bug_id,
          "status": "closed", "fixed_in": version})
