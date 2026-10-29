"""将 develop 未共享工作保存在 adhoc worktree，再对齐本地 develop。"""
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.foundation.textutil import slugify
from mdf_core.lifecycle.delivery_state import read_json, write_json
from mdf_core.lifecycle.publish import state_path
from mdf_core.workspace.gitutil import (
    ensure_clean, primary_worktree, repo_path, require_git_root, sibling_worktree, worktree_map,
)
from mdf_core.workspace.merge_policy import ancestor, configured, git, sha


def record_path(repo):
    return state_path(repo, "dev-pr").parent.parent / "dev-pr.json"


def pending(repo):
    path = record_path(repo)
    if not path.exists():
        return None
    state = read_json(path)
    finish = state_path(repo, state["source"])
    done = read_json(finish) if finish.exists() else {}
    if done.get("completed") and done.get("source") == state["source"]:
        return None
    return state


def prepare(repo, slug=None, *, expected_head=None, expected_base=None):
    """只准备本地现场；审查、验证与平台操作由 intent 委托现有 PR 流程。"""
    repo = primary_worktree(repo)
    state = pending(repo)
    if configured(repo, state["head"] if state else None)["mode"] != "pr":
        raise MDFError("dev-pr 仅用于 PR mode", code="pr_mode_required")
    identity = {
        "fetch": git(repo, "remote", "get-url", "--all", "origin").stdout,
        "push": git(repo, "remote", "get-url", "--push", "--all", "origin").stdout,
    }
    if state is None:
        head, base = sha(repo, "refs/heads/develop"), sha(repo, "refs/remotes/origin/develop")
        if ((expected_head is not None and head != expected_head)
                or (expected_base is not None and base != expected_base)):
            raise MDFError("develop 与已确认计划不符", code="sync_plan_changed")
        if ancestor(repo, head, base):
            return {"status": "no_pending_commits", "completed": True}
        bases = git(repo, "merge-base", "--all", head, base).stdout.split()
        if len(bases) != 1:
            raise MDFError("dev-pr 需要唯一 merge-base", code="ambiguous_base")
        slug = slug or f"develop-{head[:12]}"
        if slugify(slug) != slug:
            raise MDFError("dev-pr slug 必须为 kebab slug", code="invalid_slug")
        source = f"adhoc/{slug}"
        work = sibling_worktree(repo, source)
        if (work.exists() or not git(repo, "show-ref", "--verify", "--quiet",
                                    f"refs/heads/{source}", check=False).returncode
                or git(repo, "ls-remote", "origin", f"refs/heads/{source}").stdout.strip()):
            raise MDFError("adhoc 分支或 worktree 已存在", code="collision")
        occupant = worktree_map(repo).get("develop")
        if occupant:
            ensure_clean(occupant)
        state = {"source": source, "head": head, "base": base, "merge_base": bases[0],
                 "worktree": str(work), "identity": identity, "reset": False}
        write_json(record_path(repo), state)
    elif state["identity"] != identity or (slug and state["source"] != f"adhoc/{slug}"):
        raise MDFError("dev-pr 恢复目标已变化，保留现场", code="pull_state_changed")

    work = Path(state["worktree"])
    source = state["source"]
    if not state["reset"]:
        current = sha(repo, "refs/heads/develop")
        if current not in (state["head"], state["base"]):
            raise MDFError("develop 出现新提交，保留现场", code="pull_state_changed")
        occupant = worktree_map(repo).get("develop")
        if occupant:
            ensure_clean(occupant)
        ref = git(repo, "rev-parse", "--verify", f"refs/heads/{source}", check=False)
        if ref.returncode:
            git(repo, "branch", source, state["head"])
        elif ref.stdout.strip() != state["head"]:
            raise MDFError("adhoc 未保留原 develop HEAD", code="pull_state_changed")
        owner = worktree_map(repo).get(source)
        if owner is None and not work.exists():
            work.parent.mkdir(parents=True, exist_ok=True)
            git(repo, "worktree", "add", str(work), source)
        elif owner != work:
            raise MDFError("adhoc worktree 与记录不符", code="pull_state_changed")
        ensure_clean(work)
        # reset --keep 保留意外出现的未提交修改；未 checkout 的 ref 使用 CAS。
        if current != state["base"]:
            if sha(repo, "refs/heads/develop") != state["head"]:
                raise MDFError("develop 在准备期间变化", code="pull_state_changed")
            if occupant:
                git(occupant, "reset", "--keep", state["base"])
            else:
                git(repo, "update-ref", "refs/heads/develop", state["base"], state["head"])
        state["reset"] = True
        write_json(record_path(repo), state)
    return {**state, "status": "dev_pr_required", "completed": False, "next_intent": "dev-pr"}


def command_dev_pr(args):
    from mdf_core.lifecycle.pull_finish import finish_lock
    repo = repo_path(args.repo)
    require_git_root(repo)
    with finish_lock(repo):
        git(repo, "fetch", "origin", "--prune")
        emit({"ok": True, "operation": "dev-pr", "result": prepare(repo, args.slug)})
