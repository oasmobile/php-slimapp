"""Deterministic Git init and no-ff merge for skill workflows."""

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    current_branch,
    ensure_clean,
    forget_git_root,
    git_in_progress_head,
    git_root,
    repo_path,
    require_git_root,
    run,
)


def command_prepare_git(args) -> None:
    path = repo_path(args.repo)
    root = git_root(path)
    if root is not None and root != path:
        raise MDFError(
            f"位于其他仓库内部（{root}），不嵌套 git init",
            code="nested_git",
            details={"git_root": str(root)},
        )
    created = False
    if root is None:
        result = run(
            ["git", "init", "--initial-branch=master", "--template="],
            cwd=path,
            check=False,
        )
        if result.returncode:
            raise MDFError(
                result.stderr.strip() or "git init 失败",
                code="git_init_failed",
            )
        created = True
        forget_git_root(path)
    require_git_root(path)
    emit(
        {
            "ok": True,
            "operation": "prepare-git",
            "created": created,
            "git_root": str(path),
            "branch": current_branch(path),
        }
    )


def command_merge_no_ff(args) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_clean(repo)
    source = args.commit
    from mdf_core.workspace.merge_policy import require_merge
    require_merge(repo, source, current_branch(repo))
    verified = run(
        ["git", "rev-parse", "--verify", source],
        cwd=repo,
        check=False,
    )
    if verified.returncode:
        raise MDFError(f"无法解析合并目标 {source}", code="bad_commit")
    from mdf_core.workspace.squash import require_ready
    require_ready(repo)
    incoming = run(
        ["git", "for-each-ref", "--format=%(refname)",
         f"--points-at={verified.stdout.strip()}", "refs/heads"], cwd=repo,
    ).stdout.splitlines()
    for branch in incoming:
        require_ready(repo, branch.removeprefix("refs/heads/"))
    before = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    result = run(["git", "merge", "--no-ff", source], cwd=repo, check=False)
    if result.returncode:
        raise MDFError(
            "no-ff 合并冲突，保留现场",
            code="merge_conflict",
            details={"head": git_in_progress_head(repo)},
        )
    after = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    emit(
        {
            "ok": True,
            "operation": "merge-no-ff",
            "merged": before != after,
            "commit": after,
            "branch": current_branch(repo),
        }
    )
