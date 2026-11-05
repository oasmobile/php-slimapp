"""fact 前的 hook 执行与实际改动分类；补审补测由 Agent 承办。"""
import re
import stat
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    branch_details,
    current_branch,
    ensure_clean,
    repo_path,
    require_git_root,
    run,
)
from mdf_core.workspace.hooks import FINISH_HOOK, run_hook
from mdf_core.foundation.paths import load_manifest


def changes_since(repo, before_head):
    if not re.fullmatch(r"[0-9a-f]{40}", before_head):
        raise MDFError("--after 必须为 hook 前的完整 commit hash", code="invalid_hook_base")
    run(["git", "merge-base", "--is-ancestor", before_head, "HEAD"], cwd=repo)
    tracked = run(
        ["git", "diff", "--name-only", "-z", "--no-renames", before_head, "--"], cwd=repo,
    ).stdout
    staged = run(
        ["git", "diff", "--cached", "--name-only", "-z", "--no-renames", before_head, "--"],
        cwd=repo,
    ).stdout
    untracked = run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=repo,
    ).stdout
    paths = sorted(set((tracked + staged + untracked).split("\0")) - {""})
    entries = run(["git", "ls-tree", "-r", "-z", before_head], cwd=repo).stdout
    old_modes = {}
    for entry in entries.split("\0"):
        if entry:
            metadata, name = entry.split("\t", 1)
            old_modes[name] = int(metadata.split()[0], 8)
    index_modes = {}
    for entry in run(["git", "ls-files", "--stage", "-z"], cwd=repo).stdout.split("\0"):
        if entry:
            metadata, name = entry.split("\t", 1)
            index_modes.setdefault(name, []).append(int(metadata.split()[0], 8))

    def document(name):
        path = Path(name)
        if path.suffix != ".md" or (len(path.parts) > 1 and path.parts[0] not in {"docs", "changes"}):
            return False
        modes = [old_modes[name]] if name in old_modes else []
        modes.extend(index_modes.get(name, []))
        target = repo / name
        if any(parent.is_symlink() for parent in target.parents if parent != repo):
            return False
        if target.exists() or target.is_symlink():
            modes.append(target.lstat().st_mode)
        return bool(modes) and all(stat.S_ISREG(mode) and not mode & 0o111 for mode in modes)

    return {"changed_paths": paths, "needs_recheck": any(not document(name) for name in paths)}


def command_pre_gitflow_finish(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    branch = current_branch(repo)
    if not branch_details(branch)["supported"]:
        raise MDFError("hook 只在 owner 交付分支执行", code="unsupported_branch")
    if branch_details(branch)["kind"] == "adhoc":
        from mdf_core.lifecycle.adhoc_context import require_source
        require_source(branch)
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("hook 要求 manifest state 为 ready", code="manifest_not_ready")
    if args.after is not None:
        emit({"ok": True, "operation": FINISH_HOOK, "before_head": args.after,
              **changes_since(repo, args.after)})
        return
    ensure_clean(repo)
    before_head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    hook = run_hook(
        repo, FINISH_HOOK, context={"branch": branch, "before_head": before_head},
        env={"MDF_WORKTREE": str(repo), "MDF_BRANCH": branch, "MDF_BEFORE_HEAD": before_head},
        continuation="继续按实际改动决定后续流程",
    )
    if current_branch(repo) != branch:
        raise MDFError("hook 改变了当前分支；保留现场", code="hook_branch_changed")
    result = {"ok": True, "operation": FINISH_HOOK, "before_head": before_head,
              "hook": hook or {"name": FINISH_HOOK, "status": "skipped"}}
    if result["hook"]["status"] != "pending":
        result.update(changes_since(repo, before_head))
    emit(result)
