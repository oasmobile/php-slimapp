"""常驻 planning 分支与 sibling worktree。"""

from __future__ import annotations

from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    current_branch,
    ensure_clean,
    git_in_progress_head,
    git_is_clean,
    primary_worktree,
    repo_path,
    require_git_root,
    run,
    sibling_worktree,
    worktree_map,
)


BRANCH = "planning"


def _git(repo: Path, *args: str, check: bool = True):
    return run(["git", *args], cwd=repo, check=check)


def _exists(repo: Path, ref: str) -> bool:
    return not _git(repo, "rev-parse", "--verify", "--quiet", ref,
                    check=False).returncode


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return _git(
        repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False,
    ).returncode == 0


def merge_branch(repo: Path, source: str) -> bool:
    """develop 与 planning：能 fast-forward 则 ff，已分叉则 no-ff。"""
    if git_in_progress_head(repo) == "MERGE_HEAD":
        raise MDFError(
            "未结束的合并（MERGE_HEAD 仍在）；"
            "先完成提交或执行 git merge --abort",
            code="unfinished_merge",
        )
    if _is_ancestor(repo, source, "HEAD"):
        return False
    from mdf_core.workspace.merge_policy import configured, require_merge
    require_merge(repo, source, current_branch(repo))
    if _is_ancestor(repo, "HEAD", source) and configured(repo)["mode"] != "pr":
        _git(repo, "merge", "--ff-only", source)
        return True
    result = _git(repo, "merge", "--no-ff", "--no-commit", source, check=False)
    if result.returncode:
        if (
            result.returncode != 1
            and git_in_progress_head(repo) == "MERGE_HEAD"
        ):
            raise MDFError(
                "未结束的合并（MERGE_HEAD 仍在）；"
                "先完成提交或执行 git merge --abort",
                code="unfinished_merge",
            )
        _git(repo, "merge", "--abort", check=False)
        raise MDFError(
            f"Merge conflict: {source} -> {current_branch(repo)}; "
            "merge was aborted",
            code="merge_conflict",
        )
    if not _git(repo, "status", "--porcelain").stdout.strip():
        if git_in_progress_head(repo) == "MERGE_HEAD":
            _git(repo, "merge", "--abort", check=False)
        return False
    target = current_branch(repo)
    _git(repo, "commit", "-m",
         f"chore(planning): 合并 {source} 到 {target}")
    return True


def command_planning(args) -> None:
    if args.action == "ensure":
        command_planning_ensure(args)
        return
    command_planning_land(args)


def command_planning_ensure(args) -> None:
    emit(ensure_planning(repo_path(args.repo)))


def ensure_planning(repo: Path) -> dict:
    require_git_root(repo)
    if not _exists(repo, "refs/heads/develop"):
        raise MDFError("Branch develop must exist", code="missing_branch")
    primary = primary_worktree(repo)
    path = sibling_worktree(repo, BRANCH)
    trees = worktree_map(primary)
    occupant = trees.get(BRANCH)
    created = False
    if occupant is not None:
        if occupant.resolve() != path.resolve():
            raise MDFError(
                "planning 已被其他 worktree 占用",
                code="planning_occupied",
            )
        work = occupant
    else:
        if path.exists():
            raise MDFError("并行分支或 worktree 已存在", code="collision")
        path.parent.mkdir(parents=True, exist_ok=True)
        if _exists(repo, f"refs/heads/{BRANCH}"):
            _git(primary, "worktree", "add", str(path), BRANCH)
        else:
            _git(primary, "worktree", "add", "-b", BRANCH, str(path), "develop")
        created = True
        work = path
    synced = False
    if git_is_clean(work):
        merge_branch(work, "develop")
        synced = True
    return {
        "ok": True,
        "operation": "planning-ensure",
        "branch": BRANCH,
        "worktree": str(work),
        "created": created,
        "synced": synced,
    }


def command_planning_land(args) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    if not _exists(repo, f"refs/heads/{BRANCH}"):
        raise MDFError("Branch planning must exist", code="missing_branch")
    primary = primary_worktree(repo)
    trees = worktree_map(primary)
    occupant = trees.get("develop")
    if occupant is None:
        raise MDFError(
            "需要主 worktree 占用 develop 才能合入规划",
            code="develop_unoccupied",
        )
    planning_wt = trees.get(BRANCH)
    if planning_wt is not None and occupant.resolve() == planning_wt.resolve():
        raise MDFError(
            "develop 不能占用 planning worktree",
            code="planning_occupied",
        )
    ensure_clean(occupant)
    if planning_wt is not None:
        ensure_clean(planning_wt)
    from mdf_core.workspace.squash import require_ready
    require_ready(planning_wt or primary, BRANCH)
    landed = merge_branch(occupant, BRANCH)
    synced = False
    if planning_wt is not None and git_is_clean(planning_wt):
        merge_branch(planning_wt, "develop")
        synced = True
    emit({
        "ok": True,
        "operation": "planning-land",
        "landed": landed,
        "synced": synced,
    })
