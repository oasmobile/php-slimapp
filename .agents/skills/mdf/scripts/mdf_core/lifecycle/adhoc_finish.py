"""Adhoc 本地合并及有限恢复；Change 与账本共用实际 Git 完成证据。"""
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.lifecycle.adhoc_context import context, material, require_source
from mdf_core.lifecycle.delivery_state import read_json, write_json
from mdf_core.lifecycle.publish import state_path
from mdf_core.workspace.gitutil import ensure_clean, primary_worktree, worktree_map
from mdf_core.workspace.merge_policy import ancestor, configured, git, sha


def _record(repo, source):
    path = state_path(repo, source)
    state = read_json(path) if path.exists() else None
    if state and (state.get("source") != source or state.get("target") != "develop"
                  or state.get("mode") not in {"local", "pr"}):
        raise MDFError("Adhoc 操作记录身份不符", code="finish_state_changed")
    return path, state


def status(repo, source, slug=None):
    require_source(source)
    path, state = _record(repo, source)
    branch = git(repo, "branch", "--show-current").stdout.strip()
    head = sha(repo, "HEAD")
    mode = configured(repo)["mode"]
    if state and state["mode"] != mode:
        raise MDFError("Adhoc 收口模式已变化", code="finish_state_changed")
    completed = False
    merged = (state or {}).get("merge_commit")
    if state and merged:
        ensure_clean(repo)
        if not branch and head != state["head"]:
            raise MDFError("保留工作区已偏离原交付 tip", code="finish_state_changed")
        first = git(repo, "rev-list", "--first-parent", "develop" if mode == "local" else "origin/develop").stdout.split()
        parents = git(repo, "show", "-s", "--format=%P", merged).stdout.split()
        if merged not in first or len(parents) != 2 or parents[1] != state["head"]:
            raise MDFError("Adhoc 合并证据已变化", code="finish_state_changed")
        exists = git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{source}", check=False).returncode == 0
        completed = state.get("completed") is True and not exists
        if mode == "pr":
            completed = completed and (state.get("remote_cleanup") or {}).get("status") == "deleted"
    if branch != source and not merged:
        raise MDFError("adhoc-status 必须绑定本次 owner 或已有收口记录", code="stage_branch")
    result = context(repo, source, slug, head=state["head"] if merged else head)
    result.update(completed=completed, merge_commit=merged,
                  next_step=None if completed else ("close-out" if mode == "local" or merged else "pr"),
                  owner_worktree=str(repo), primary_worktree=str(primary_worktree(repo)))
    if not state and ancestor(repo, head, result["range"]["target_head"]):
        result.update(next_step=None, no_pending_commits=True)
    return result


def finish(repo, source, *, recovering=False):
    from mdf_core.lifecycle.pull_finish import finish_lock

    with finish_lock(repo):
        _finish(repo, source, recovering=recovering)


def _finish(repo, source, *, recovering):
    from mdf_core.lifecycle.adhoc import completion, merged_commit
    from mdf_core.lifecycle.pull_finish import cleanup
    from mdf_core.workspace.gitflow import _merge

    require_source(source)
    path, state = _record(repo, source)
    if state and state["mode"] != "local":
        raise MDFError("本地收口记录模式不符", code="finish_state_changed")
    if recovering and state is None:
        raise MDFError("--source 恢复需要匹配的本地操作记录", code="finish_state_changed")
    if state is None:
        trees = worktree_map(repo)
        owner = trees.get(source, repo)
        ensure_clean(owner)
        ensure_clean(trees.get("develop", owner))
        root, ledger = material(repo, source)
        head = sha(repo, f"refs/heads/{source}")
        merged = merged_commit(repo, head) if ledger else None
        if ancestor(repo, head, sha(repo, "develop")) and not merged:
            raise MDFError("没有未合入提交；不创建 Change 或删除分支", code="no_pending_commits")
        completion(repo, source)
        state = {"mode": "local", "source": source, "target": "develop", "head": head,
                 "target_before": sha(repo, "develop"), "merge_commit": merged, "completed": False,
                 "retained_worktree": str(worktree_map(repo).get(source, repo)),
                 "material_path": str(root.relative_to(repo))}
        write_json(path, state)
    head = state["head"]
    current = git(repo, "rev-parse", "--verify", f"refs/heads/{source}", check=False)
    if state.get("completed") and current.returncode == 0:
        raise MDFError("已收口的同名分支被重新创建，保留现场", code="finish_state_changed")
    if not current.returncode and current.stdout.strip() != head:
        raise MDFError("源分支已变化，保留现场", code="finish_state_changed")
    owner = Path(state["retained_worktree"])
    ensure_clean(owner)
    target = worktree_map(repo).get("develop", owner)
    ensure_clean(target)
    merged = state.get("merge_commit")
    if merged is None:
        # merge 成功而记录尚未写入时，只接受精确的双亲结果。
        candidate = merged_commit(repo, head)
        if candidate:
            parents = git(repo, "show", "-s", "--format=%P", candidate).stdout.split()
            if parents != [state["target_before"], head]:
                raise MDFError("未记录的目标变化，保留现场", code="finish_state_changed")
            merged = candidate
        else:
            if sha(repo, "develop") != state["target_before"] or current.returncode:
                raise MDFError("目标或源分支已变化，重新核验后再收口", code="finish_state_changed")
            _merge(target, head, "develop")
            merged = sha(repo, "develop")
        state["merge_commit"] = merged
        write_json(path, state)
    parents = git(repo, "show", "-s", "--format=%P", merged).stdout.split()
    first = git(repo, "rev-list", "--first-parent", "develop").stdout.split()
    if merged not in first or len(parents) != 2 or parents[1] != head:
        raise MDFError("合并结果与源提交不符", code="finish_state_changed")
    cleanup(repo, state)
    primary = primary_worktree(repo)
    if owner != primary and sha(owner, "HEAD") == merged:
        git(owner, "checkout", "--detach", head)
    elif owner == primary and not git(owner, "branch", "--show-current").stdout.strip():
        if "develop" not in worktree_map(repo):
            git(owner, "checkout", "develop")
    state["completed"] = True
    write_json(path, state)
    emit({"ok": True, "operation": "finish-gitflow", "mode": "local", "source": source,
          "targets": ["develop"], "completed": True, "merge_commit": merged, "deleted": source,
          "retained_worktree": str(owner), "primary_worktree": str(primary), "tag": None, "pushed": False})
