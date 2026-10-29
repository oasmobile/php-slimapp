"""按 roster 将 qa/dev 角色分支合流回 owner（roster-join）。"""
from mdf_core.lifecycle.delivery_state import (
    fingerprints,
    git,
    matches,
    committed_design,
    read_json,
    safe,
    write_json,
)
from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import current_branch, ensure_clean, worktree_map
from mdf_core.lifecycle.roster import merge_branches, role_branches


def roster_join(repo, root, data, approval, qa_branch=None, dev_branch=None):
    ensure_clean(repo)
    current = committed_design(repo, root, data)
    if current_branch(repo) != data["branch"]:
        raise MDFError("仅 owner 可 roster-join", code="stage_branch")
    policy = read_json(safe(repo, root / "design-policy.json"))
    receipt_path = safe(repo, root / "gates/roster-join.json")
    receipt = read_json(receipt_path) if receipt_path.exists() else None
    expected_names = role_branches(data["branch"], data["roster"])
    qa_merged = merge_branches(
        "qa", data["branch"], data["roster"], qa_branch,
    )
    dev_merged = merge_branches(
        "dev", data["branch"], data["roster"], dev_branch,
    )
    merged = [*qa_merged, *dev_merged]
    if receipt is not None:
        if (receipt.get("design") != current["design"]
                or set(receipt.get("branches", {})) != set(expected_names)
                or set(receipt.get("merged", [])) != set(merged)):
            raise MDFError("roster-join 记录与当前交付不一致",
                           code="stale_roster_join")
        for branch, head in receipt["branches"].items():
            if branch in receipt.get("merged", []):
                if git(repo, "merge-base", "--is-ancestor", head, "HEAD",
                       check=False).returncode:
                    raise MDFError("roster-join 提交不在 owner 历史中",
                                   code="stale_roster_join")
            ref = git(repo, "rev-parse", "--verify", f"refs/heads/{branch}",
                      check=False)
            if not ref.returncode and ref.stdout.strip() != head:
                raise MDFError("角色分支在 roster-join 后变化",
                               code="stale_roster_join")
        return cleanup(repo, expected_names)
    worktrees = worktree_map(repo)
    for branch in expected_names:
        if git(repo, "show-ref", "--verify", f"refs/heads/{branch}",
               check=False).returncode:
            raise MDFError(f"缺少角色分支 {branch}", code="missing_role")
        if branch in worktrees:
            ensure_clean(worktrees[branch])
    for branch, stage, role in (
        *((name, "write-tests", "qa") for name in qa_merged),
        *((name, "implement", "dev") for name in dev_merged),
    ):
        if branch not in worktrees:
            raise MDFError(f"缺少角色 worktree {branch}", code="missing_role")
        role_repo = worktrees[branch]
        from mdf_core.lifecycle.delivery_state import locate
        role_root, role_data = locate(role_repo)
        if committed_design(role_repo, role_root, role_data)["design"] != current["design"]:
            raise MDFError("角色分支没有共同设计基线", code="stale_gate")
        common = git(repo, "merge-base", "HEAD", branch).stdout.strip()
        changed = git(repo, "diff", "--name-only", common, branch).stdout.splitlines()
        protected = [name for name in changed
                     if matches(name, policy["protected_paths"])
                     or name == ".mdf/manifest.yaml"]
        if role == "dev" and protected and not approval:
            raise MDFError("实现分支修改了测试或验证规则",
                           code="test_approval_required",
                           details={"paths": protected})
    from mdf_core.workspace.squash import require_ready
    require_ready(repo)
    for branch in merged:
        require_ready(worktrees[branch])
    for branch in qa_merged:
        merge_role(repo, root, branch)
    # 多路 qa 的 write-tests 记录冲突时只保留第一路；converge 以合并后的测试为基线。
    tests = fingerprints(repo, root, data)["tests"]
    for branch in dev_merged:
        merge_role(repo, root, branch)
    receipt = {
        "design": current["design"],
        "tests": tests,
        "merged": merged,
        "branches": {
            branch: git(repo, "rev-parse", f"refs/heads/{branch}").stdout.strip()
            for branch in expected_names
        },
    }
    write_json(receipt_path, receipt)
    git(repo, "add", "--", str(receipt_path.relative_to(repo)))
    git(repo, "commit", "-m", "chore(delivery): 固定 roster-join 收据")
    return cleanup(repo, expected_names)


def merge_role(repo, root, branch):
    from mdf_core.workspace.squash import require_ready
    require_ready(repo)
    require_ready(repo, branch)
    if not git(repo, "merge-base", "--is-ancestor", branch, "HEAD",
                check=False).returncode:
        return
    result = git(repo, "merge", "--no-ff", "--no-commit", branch, check=False)
    if result.returncode:
        unmerged = git(repo, "diff", "--name-only", "--diff-filter=U"
                       ).stdout.splitlines()
        allowed = {
            str((root / "gates" / name).relative_to(repo))
            for name in ("write-tests.json", "implement.json")
        }
        if not unmerged or set(unmerged) - allowed:
            raise MDFError("roster-join 冲突，保留现场；涉及测试的解决需用户确认",
                           code="merge_conflict")
        for path in unmerged:
            git(repo, "checkout", "--ours", "--", path)
            git(repo, "add", "--", path)
    git(repo, "commit", "-m", f"chore(delivery): roster-join {branch}")


def cleanup(repo, branches):
    worktrees = worktree_map(repo)
    for branch in branches:
        if branch in worktrees:
            ensure_clean(worktrees[branch])
            git(repo, "worktree", "remove", str(worktrees[branch]))
        if not git(repo, "show-ref", "--verify", f"refs/heads/{branch}",
                   check=False).returncode:
            git(repo, "branch", "-D", branch)
    return {"joined": list(branches)}
