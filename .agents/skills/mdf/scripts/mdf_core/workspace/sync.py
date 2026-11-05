"""三大 trunk（master / develop / planning）与 origin 对齐：先拉后推。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    current_branch,
    ensure_clean,
    git_in_progress_head,
    primary_worktree,
    repo_path,
    require_git_root,
    run,
    worktree_map,
)

ORIGIN = "origin"
TRUNKS = ("master", "develop", "planning")


def _git(repo: Path, *args: str, check: bool = True):
    return run(["git", *args], cwd=repo, check=check)


def _exists(repo: Path, ref: str) -> bool:
    return not _git(
        repo, "rev-parse", "--verify", "--quiet", ref, check=False
    ).returncode


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return _git(
        repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False,
    ).returncode == 0


def _sha(repo: Path, ref: str) -> str:
    return _git(repo, "rev-parse", ref).stdout.strip()


def _require_origin(repo: Path) -> None:
    if _git(repo, "remote", "get-url", ORIGIN, check=False).returncode:
        raise MDFError("sync 需要 remote origin", code="missing_origin")


def _local_heads(repo: Path) -> list[str]:
    raw = _git(
        repo, "for-each-ref", "--format=%(refname)", "refs/heads",
    ).stdout
    return [line.removeprefix("refs/heads/") for line in raw.splitlines() if line]


def _remote_heads(repo: Path) -> list[str]:
    raw = _git(
        repo, "for-each-ref", "--format=%(refname)",
        f"refs/remotes/{ORIGIN}",
    ).stdout
    names: list[str] = []
    for line in raw.splitlines():
        name = line.removeprefix(f"refs/remotes/{ORIGIN}/")
        if name and name != "HEAD":
            names.append(name)
    return names


def _relationship_graph(repo: Path, name: str, info: dict[str, Any], refs: list[str]) -> str:
    local = f"o {str(info['local'])[:12]} (local refs/heads/{name})"
    remote = f"o {str(info['remote'])[:12]} (remote refs/remotes/{ORIGIN}/{name})"
    relation = info["relation"]
    if relation == "local_only":
        return local
    if relation == "remote_only":
        return remote
    if relation == "equal":
        return f"{local} = {remote}"
    if relation == "ahead":
        return f"{remote}\n| +{info['ahead']} commit\n{local}"
    if relation == "behind":
        return f"{local}\n| +{info['behind']} commit\n{remote}"
    bases = _git(repo, "merge-base", "--all", *refs, check=False).stdout.split()
    if not bases:
        return f"{local}\n{remote}\n（无共同祖先，不可普通 merge）"
    base = "、".join(sha[:12] for sha in bases)
    return (f"共同祖先 {base}\n"
            f"├── +{info['ahead']} commit ── {local}\n"
            f"└── +{info['behind']} commit ── {remote}")


def _preview(repo: Path, *, pr: bool = False) -> dict[str, Any]:
    local = set(_local_heads(repo))
    remote = set(_remote_heads(repo))
    branches = {}
    for name in sorted(local | remote):
        refs = []
        info = {"sync": name in TRUNKS}
        for side, exists, ref in (
            ("local", name in local, f"refs/heads/{name}"),
            ("remote", name in remote, f"refs/remotes/{ORIGIN}/{name}"),
        ):
            info[side] = _sha(repo, ref) if exists else None
            if exists:
                refs.append(ref)
        if len(refs) == 2:
            ahead, behind = map(int, _git(
                repo, "rev-list", "--left-right", "--count", f"{refs[0]}...{refs[1]}",
            ).stdout.split())
            relation = ("diverged" if ahead and behind else
                        "ahead" if ahead else "behind" if behind else "equal")
            info.update(ahead=ahead, behind=behind, relation=relation)
        else:
            info.update(ahead=None, behind=None,
                        relation="local_only" if name in local else "remote_only")
        info["graph"] = _relationship_graph(repo, name, info, refs)
        branches[name] = info
    from mdf_core.workspace.sync_pull import plans
    pull_plan = plans(repo, branches)
    snapshot = "\0".join([
        str(repo),
        _git(repo, "remote", "get-url", "--all", ORIGIN).stdout,
        _git(repo, "remote", "get-url", "--push", "--all", ORIGIN).stdout,
        *(f"{name}:{branches[name]['local']}:{branches[name]['remote']}" for name in TRUNKS),
        json.dumps({"pr": pr, "pull_plan": pull_plan}, sort_keys=True),
    ])
    return {
        "ok": True, "operation": "sync-preview", "branches": branches,
        "confirmation": hashlib.sha256(snapshot.encode()).hexdigest(),
        "pr": pr, "pull_plan": pull_plan,
        "extra_local": sorted(local - set(TRUNKS)),
        "extra_remote": sorted(remote - set(TRUNKS)),
    }


def _pull_into(work: Path, branch: str) -> str:
    """把 origin/<branch> 合入当前 checkout；返回 noop / ff / merged。"""
    remote = f"refs/remotes/{ORIGIN}/{branch}"
    if git_in_progress_head(work) == "MERGE_HEAD":
        raise MDFError(
            "未结束的合并（MERGE_HEAD 仍在）；"
            "先完成提交或执行 git merge --abort",
            code="unfinished_merge",
        )
    if current_branch(work) != branch:
        _git(work, "checkout", branch)
    if _is_ancestor(work, remote, "HEAD"):
        return "noop"
    if _is_ancestor(work, "HEAD", remote):
        _git(work, "merge", "--ff-only", remote)
        return "ff"
    result = _git(
        work, "merge", "--no-ff", "--no-commit", remote, check=False,
    )
    if result.returncode:
        conflicts = [name for name in _git(
            work, "diff", "--name-only", "--diff-filter=U", "-z",
        ).stdout.split("\0") if name]
        raise MDFError(
            f"合并失败: {remote} -> {branch}；保留现场，先尝试解决 conflict",
            code="merge_conflict" if conflicts else "git_failed",
            details={"branch": branch, "worktree": str(work), "conflicts": conflicts,
                     "stdout": result.stdout, "stderr": result.stderr},
        )
    _git(
        work, "commit", "-m",
        f"chore(sync): 合并 {ORIGIN}/{branch} 到 {branch}",
    )
    return "merged"


def command_sync(args) -> None:
    from mdf_core.lifecycle.pull_finish import finish_lock
    with finish_lock(repo_path(args.repo)):
        _command_sync(args)


def _command_sync(args) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    _require_origin(repo)
    primary = primary_worktree(repo)
    _git(primary, "fetch", ORIGIN, "--prune")

    for branch in TRUNKS:
        local = f"refs/heads/{branch}"
        remote = f"refs/remotes/{ORIGIN}/{branch}"
        if not _exists(primary, local) or not _exists(primary, remote):
            raise MDFError(
                f"Branch {branch} and {ORIGIN}/{branch} must both exist",
                code="missing_upstream_branch",
            )

    preview = _preview(primary, pr=args.pr)
    if not args.confirm:
        emit(preview)
        return
    if args.confirm != preview["confirmation"]:
        raise MDFError(
            "分支关系或同步目标已变化；重新展示图并请用户确认", code="sync_plan_changed", details=preview,
        )

    if preview["pull_plan"] and not args.pr:
        raise MDFError("需要 PR/MR；用 sync --pr 重新预览、确认后提交或恢复", code="pr_required",
                       details=preview)

    trees = worktree_map(primary)
    need_primary = False
    for branch in TRUNKS:
        occupant = trees.get(branch)
        if occupant is not None:
            ensure_clean(occupant)
        else:
            need_primary = True
    if need_primary:
        ensure_clean(primary)

    if preview["pull_plan"]:
        from mdf_core.workspace.sync_pull import advance
        pulls = advance(primary, preview["pull_plan"],
                        {name: preview["branches"][name]["remote"] for name in TRUNKS})
        completed = all(item["status"] == "completed" for item in pulls.values())
        refreshed = _preview(primary, pr=args.pr)
        emit({"ok": True, "operation": "sync", "completed": False,
              "status": ("dev_pr_required" if any(item["status"] == "dev_pr_required" for item in pulls.values())
                         else "ready_to_sync" if completed else "waiting_for_pr"),
              "pull_requests": pulls, "preview": refreshed,
              "extra_local": refreshed["extra_local"], "extra_remote": refreshed["extra_remote"]})
        return

    extras_local = sorted(name for name in _local_heads(primary)
                          if name not in TRUNKS)
    extras_remote = sorted(name for name in _remote_heads(primary)
                           if name not in TRUNKS)

    original = current_branch(primary) if need_primary else None
    trunks: dict[str, Any] = {}
    try:
        for branch in TRUNKS:
            work = trees.get(branch) or primary
            before_remote = _sha(primary, f"refs/remotes/{ORIGIN}/{branch}")
            before_local = _sha(primary, f"refs/heads/{branch}")
            pull = _pull_into(work, branch)
            after_local = _sha(primary, f"refs/heads/{branch}")
            trunks[branch] = {
                "pull": pull,
                "before": before_local,
                "after": after_local,
                "origin_before": before_remote,
                "worktree": str(work),
            }
    finally:
        if (original is not None and current_branch(primary) != original
                and git_in_progress_head(primary) is None):
            _git(primary, "checkout", original)

    refspecs = [f"refs/heads/{branch}:refs/heads/{branch}" for branch in TRUNKS]
    _git(primary, "push", "--atomic", "--no-follow-tags", ORIGIN, *refspecs)
    for branch, info in trunks.items():
        info["push"] = (
            "noop" if info["after"] == info["origin_before"] else "updated"
        )

    emit({
        "ok": True,
        "operation": "sync",
        "trunks": trunks,
        "extra_local": extras_local,
        "extra_remote": extras_remote,
    })
