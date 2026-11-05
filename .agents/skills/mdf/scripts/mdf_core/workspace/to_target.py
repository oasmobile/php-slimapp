"""解析 to 目标：别名、已有 worktree，或为已有分支建树。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    git_in_progress_head,
    primary_worktree,
    repo_path,
    require_git_root,
    run,
    sibling_worktree,
    worktree_map,
)
from mdf_core.workspace.planning import ensure_planning


PLANNING_ALIASES = frozenset({"plan", "planning", "plan-mode"})
DEVELOP_ALIASES = frozenset({"develop"})
DEPLOY_ALIASES = frozenset({"deploy"})
DEPLOY_BRANCH = "master"


def _normalize(target: str) -> str:
    return target.strip().lower().replace("_", "-").replace(" ", "-")


def _exists(repo: Path, ref: str) -> bool:
    return not run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=repo,
        check=False,
    ).returncode


def command_to(args: Any) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    raw = (args.target or "").strip()
    if not raw:
        raise MDFError(
            "to 需要目标", code="bad_target", details=_available(repo),
        )
    emit(_resolve(repo, raw))


def _resolve(repo: Path, raw: str) -> dict[str, Any]:
    key = _normalize(raw)
    primary = primary_worktree(repo)
    trees = worktree_map(primary)
    if key in PLANNING_ALIASES:
        result = ensure_planning(repo)
        return _payload(raw, "planning", result["branch"],
                        Path(result["worktree"]), result["created"])
    if key in DEVELOP_ALIASES:
        path = trees.get("develop")
        if path is None:
            raise MDFError(
                "没有占用 develop 的 worktree",
                code="develop_unoccupied",
                details=_available(repo),
            )
        return _payload(raw, "develop", "develop", path, False)
    if key in DEPLOY_ALIASES:
        path, created = _ensure_deploy(primary, trees)
        return _payload(raw, "deploy", DEPLOY_BRANCH, path, created)
    matches = _match_worktrees(trees, raw, key)
    paths = {path.resolve() for _, path in matches}
    if len(paths) == 1:
        branch, path = next(
            item for item in matches if item[1].resolve() in paths
        )
        return _payload(raw, None, branch, path, False)
    if len(paths) > 1:
        raise MDFError(
            "目标匹配多棵 worktree",
            code="ambiguous_target",
            details=_available(repo),
        )
    branch = _existing_branch(repo, raw)
    if branch is None:
        raise MDFError(
            "未知目标", code="unknown_target", details=_available(repo),
        )
    occupant = trees.get(branch)
    if occupant is not None:
        return _payload(raw, None, branch, occupant, False)
    path = sibling_worktree(repo, branch)
    if path.exists():
        raise MDFError("并行分支或 worktree 已存在", code="collision")
    path.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "worktree", "add", str(path), branch], cwd=primary)
    return _payload(raw, None, branch, path, True)


def _ensure_deploy(
    primary: Path, trees: dict[str, Path],
) -> tuple[Path, bool]:
    if not _exists(primary, f"refs/heads/{DEPLOY_BRANCH}"):
        raise MDFError("需要已有 master 分支", code="missing_branch")
    path = sibling_worktree(primary, "deploy")
    work = _worktree_at(primary, path)
    if work is None:
        occupant = trees.get(DEPLOY_BRANCH)
        if occupant is not None:
            raise MDFError(
                "master 已被其他 worktree 占用",
                code="master_occupied",
                details={"worktree": str(occupant)},
            )
        if path.exists():
            raise MDFError("并行分支或 worktree 已存在", code="collision")
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "worktree", "add", str(path), DEPLOY_BRANCH], cwd=primary)
        return path, True
    if _show_branch(work) == DEPLOY_BRANCH:
        return work, False
    occupant = trees.get(DEPLOY_BRANCH)
    if occupant is not None and occupant.resolve() != work.resolve():
        raise MDFError(
            "master 已被其他 worktree 占用",
            code="master_occupied",
            details={"worktree": str(occupant)},
        )
    if _tracked_dirty(work):
        raise MDFError(
            "deploy worktree 有已跟踪改动，不能切回 master",
            code="dirty_worktree",
            details={"worktree": str(work), "branch": _show_branch(work)},
        )
    run(["git", "checkout", DEPLOY_BRANCH], cwd=work)
    return work, False


def _show_branch(repo: Path) -> str:
    return run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()


def _tracked_dirty(repo: Path) -> bool:
    if git_in_progress_head(repo) is not None:
        return True
    result = run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo,
    )
    return bool(result.stdout.strip())


def _worktree_at(repo: Path, path: Path) -> Path | None:
    raw = run(["git", "worktree", "list", "--porcelain"], cwd=repo).stdout
    target = path.resolve()
    for block in raw.strip().split("\n\n"):
        for line in block.splitlines():
            if line.startswith("worktree "):
                found = Path(line.split(" ", 1)[1]).resolve()
                if found == target:
                    return found
    return None


def _payload(
    raw: str, alias: str | None, branch: str, path: Path, created: bool,
) -> dict[str, Any]:
    return {
        "ok": True,
        "operation": "to",
        "target": raw,
        "alias": alias,
        "branch": branch,
        "worktree": str(path),
        "created": created,
    }


def _match_worktrees(
    trees: dict[str, Path], raw: str, key: str,
) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for branch, path in trees.items():
        names = {branch, branch.lower(), path.name, path.name.lower()}
        if raw in names or key in {branch.lower(), path.name.lower()}:
            found.append((branch, path))
    return found


def _existing_branch(repo: Path, raw: str) -> str | None:
    for candidate in (raw, _normalize(raw)):
        if candidate and _exists(repo, f"refs/heads/{candidate}"):
            return candidate
    return None


def _available(repo: Path) -> dict[str, Any]:
    trees = worktree_map(primary_worktree(repo))
    return {
        "aliases": {
            "planning": sorted(PLANNING_ALIASES),
            "develop": sorted(DEVELOP_ALIASES),
            "deploy": sorted(DEPLOY_ALIASES),
        },
        "worktrees": {branch: str(path) for branch, path in trees.items()},
    }
