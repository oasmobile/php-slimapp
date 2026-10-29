"""核验分派目录、角色分支、共同 Git 仓库与交接证据；不写入。"""
from pathlib import Path

from mdf_core.lifecycle.delivery_state import git, locate, committed_design, design_on_ref
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    branch_details,
    current_branch,
    ensure_clean,
    repo_path,
    require_git_root,
    worktree_map,
)
from mdf_core.lifecycle.roster import owner_branch, role_branch


def common_dir(repo):
    return Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()).resolve()


def command_worktree_check(args):
    repo, owner = repo_path(args.repo), repo_path(args.owner)
    require_git_root(repo)
    require_git_root(owner)
    owner_name = current_branch(owner)
    if not branch_details(owner_name)["supported"]:
        raise MDFError("角色与 owner 交付类型不符", code="stage_branch")
    if args.role != "owner" and owner_branch(owner_name) != owner_name:
        raise MDFError("角色与 owner 交付类型不符", code="stage_branch")
    index = args.index
    if isinstance(index, bool) or not isinstance(index, int) or index < 1:
        raise MDFError("index 必须是 ≥1 的整数", code="invalid_roster")
    if args.role == "owner":
        expected = owner_name
    else:
        expected = role_branch(args.role, owner_name, index)
    trees = worktree_map(owner)
    if (current_branch(repo) != expected or trees.get(expected, Path()).resolve() != repo
            or common_dir(repo) != common_dir(owner)
            or (args.role != "owner" and repo == owner)):
        raise MDFError("worktree 身份或仓库不匹配", code="wrong_worktree")
    if args.expected_head and git(repo, "rev-parse", "HEAD").stdout.strip() != args.expected_head:
        raise MDFError("审查 HEAD 已变化", code="stale_head")
    result = {"path": str(repo), "branch": expected, "common_dir": str(common_dir(repo))}
    if args.design_commit:
        if git(repo, "merge-base", "--is-ancestor", args.design_commit, "HEAD", check=False).returncode:
            raise MDFError("角色未包含共同设计提交", code="missing_design_commit")
        root, data = locate(repo)
        owner_root, owner_data = locate(owner)
        current = committed_design(repo, root, data)
        baseline = design_on_ref(repo, root, args.design_commit)
        if (current["design"] != baseline
                or committed_design(owner, owner_root, owner_data)["design"] != baseline):
            raise MDFError("角色与 owner 的设计不同", code="stale_gate")
        roster = data["roster"]
        if args.role != "owner" and index > roster[args.role]:
            raise MDFError("index 超出 roster", code="invalid_roster")
        result["fingerprints"] = current
        if args.handoff:
            ensure_clean(repo)
            stage = {"qa": "write-tests", "dev": "implement"}.get(args.role)
            if stage is None:
                raise MDFError("交接只适用于 qa/dev", code="stage_branch")
            # clean 与 ls-files 证明产出已提交；阶段进度由调用方核对 objectives。
            git(repo, "ls-files", "--error-unmatch", str((root / "objectives.md").relative_to(repo)))
            result["head"] = git(repo, "rev-parse", "HEAD").stdout.strip()
    elif args.handoff:
        raise MDFError("交接需要固定设计提交", code="missing_design_commit")
    emit({"ok": True, "operation": "worktree-check", "result": result})
