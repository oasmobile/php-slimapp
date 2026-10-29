"""PR/MR 提交、等待、核验与清理；操作记录不充当阶段 gate。"""
from contextlib import contextmanager
import os
import re

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.integrations.forge import Forge, origin
from mdf_core.lifecycle.delivery_state import read_json, write_json
from mdf_core.lifecycle.publish import state_path
from mdf_core.lifecycle.roster import resolve_roster, role_branches
from mdf_core.workspace.gitutil import (
    branch_details, current_branch, ensure_clean, git_in_progress_head, primary_worktree, sibling_worktree, worktree_map,
)
from mdf_core.workspace.merge_policy import ancestor, git, sha


def preflight(repo, source):
    """沿用交付材料检查；由外层 intent 完成审查、验证及 fact。"""
    if current_branch(repo) != source:
        raise MDFError("首次提交或更新 PR/MR 必须在源 worktree 执行", code="stage_branch")
    kind = branch_details(source)["kind"]
    if kind == "adhoc":
        from mdf_core.lifecycle.adhoc_context import require_source
        require_source(source)
    if kind == "feature":
        from mdf_core.lifecycle.manual import feature_completion
        complete, roster = feature_completion(repo, source, allow_candidate=True)
    elif kind == "adhoc":
        from mdf_core.lifecycle.adhoc import completion
        complete, roster = None, completion(repo, source)
    else:
        complete, roster = None, resolve_roster(repo, source, kind)
    trees = worktree_map(repo)
    for name in role_branches(source, roster):
        if name in trees or not git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode:
            raise MDFError("角色分支尚未集成", code="roles_pending")
    if complete is not None:
        complete(repo)
        if git(repo, "diff", "--cached", "--name-only").stdout.strip():
            git(repo, "commit", "-m", "docs(delivery): 准备合入后的 Proposal 状态")
    ensure_clean(repo)


def verified_merge(repo, pull, source, target, head):
    if pull["source"] != source or pull["target"] != target or pull["head"] != head:
        raise MDFError("PR/MR 的来源、目标或源提交已变化", code="pull_state_changed")
    merged = sha(repo, pull["merge_commit"])
    parents = git(repo, "show", "-s", "--format=%P", merged).stdout.split()
    if len(parents) != 2 or parents[1] != head:
        raise MDFError("PR/MR 必须保留源提交并使用双亲 merge commit", code="invalid_pull_merge")
    remote = f"refs/remotes/origin/{target}"
    first = git(repo, "rev-list", "--first-parent", remote).stdout.split()
    if merged not in first:
        raise MDFError("merge commit 不在目标远端第一父链", code="pull_state_changed")
    return merged


def sync_local(repo, branch, *, integrate_develop=False):
    """默认同名 ff；close-out 可将远端集成到本地 develop，保留未共享工作。"""
    remote = f"refs/remotes/origin/{branch}"
    target = f"refs/heads/{branch}"
    remote_head = sha(repo, remote)
    occupant = worktree_map(repo).get(branch)
    if occupant:
        ensure_clean(occupant)
    local = git(repo, "rev-parse", "--verify", target, check=False)
    if local.returncode:
        git(repo, "branch", branch, remote_head)
        return
    local_head = local.stdout.strip()
    if local_head == remote_head:
        return
    if integrate_develop and branch == "develop":
        if ancestor(repo, remote_head, local_head):
            return
        if not ancestor(repo, local_head, remote_head):
            if occupant is None:
                occupant = sibling_worktree(repo, branch)
                occupant.parent.mkdir(parents=True, exist_ok=True)
                git(repo, "worktree", "add", str(occupant), branch)
            ensure_clean(occupant)
            result = git(occupant, "merge", "--no-ff", "-m",
                         "chore(closeout): 集成远端 develop 并保留本地工作", remote_head, check=False)
            if result.returncode:
                raise MDFError("本地 develop 集成失败，保留现场；解决并验证后续办 close-out",
                               code="merge_conflict" if git_in_progress_head(occupant) else "command_failed",
                               details={"worktree": str(occupant), "base": local_head,
                                        "remote_head": remote_head, "error": result.stderr.strip()})
            return
    if not ancestor(repo, local_head, remote_head):
        raise MDFError(f"本地 {branch} 与远端分歧，保留现场", code="upstream_diverged")
    if occupant:
        ensure_clean(occupant)
        git(occupant, "merge", "--ff-only", remote)
    else:
        git(repo, "update-ref", target, remote_head, local_head)


def remote_source_head(repo, source):
    ref = f"refs/heads/{source}"
    rows = git(repo, "ls-remote", "--refs", "origin", ref).stdout.splitlines()
    if not rows:
        return None
    if len(rows) != 1 or len(rows[0].split()) != 2 or rows[0].split()[1] != ref:
        raise MDFError("远端 source 查询结果不明确，保留现场", code="remote_cleanup_uncertain")
    return rows[0].split()[0]


def cleanup_remote(repo, state, path):
    """已合并且发布完成后，条件删除原远端 source；不重删不确定的分支。"""
    source, head = state["source"], state["head"]
    record = state.get("remote_cleanup")
    if record is not None and (not isinstance(record, dict) or record.get("head") != head
                               or record.get("status") not in {"pending", "deleted"}):
        raise MDFError("远端清理记录不符，保留现场", code="pull_state_changed")
    remote = remote_source_head(repo, source)
    if record is not None and remote is not None:
        if record["status"] == "deleted" or remote != head:
            raise MDFError("远端 source 已变化或被重建，保留分支", code="pull_state_changed")
        raise MDFError("上次删除结果不确定；核实并手动清理远端 source 后再续办，不得清空记录",
                       code="remote_cleanup_uncertain")
    if record is None and remote is not None:
        if state.get("completed") or remote != head:
            raise MDFError("远端 source 与本次已确认交付不符，保留分支", code="pull_state_changed")
        record = {"head": head, "status": "pending"}
        state["remote_cleanup"] = record
        write_json(path, state)
        ref = f"refs/heads/{source}"
        result = git(repo, "push", "--no-follow-tags", f"--force-with-lease={ref}:{head}",
                     "origin", f":{ref}", check=False)
        if result.returncode == 0:
            record["status"] = "deleted"
            write_json(path, state)
        remote = remote_source_head(repo, source)
        if remote is not None:
            if record["status"] == "deleted" or remote != head:
                raise MDFError("远端 source 删除时已变化或被重建，保留分支", code="pull_state_changed")
            raise MDFError("删除未确认；核实并手动清理远端 source 后再续办，不得清空记录",
                           code="remote_cleanup_uncertain", details={"error": result.stderr.strip()})
    state["remote_cleanup"] = {"head": head, "status": "deleted"}
    write_json(path, state)


def cleanup(repo, state):
    primary = primary_worktree(repo)
    source = state["source"]
    occupant = worktree_map(repo).get(source)
    if occupant is not None:
        ensure_clean(occupant)
        if sha(repo, source) != state["head"]:
            raise MDFError("源分支已变化，不能清理", code="pull_state_changed")
        git(occupant, "checkout", "--detach", state["head"])
        state["retained_worktree"] = str(occupant)
    present = git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{source}", check=False)
    if not present.returncode:
        if sha(repo, source) != state["head"]:
            raise MDFError("源分支已变化，不能删除", code="pull_state_changed")
        if source in worktree_map(repo):
            raise MDFError("源分支已被其他 worktree 占用，保留现场", code="pull_state_changed")
        deleted = git(primary, "update-ref", "-d", f"refs/heads/{source}", state["head"], check=False)
        if deleted.returncode:
            raise MDFError("源分支删除时已变化或被锁定，保留现场", code="pull_state_changed")
    remaining = git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{source}", check=False)
    if remaining.returncode == 0:
        raise MDFError("源分支已被重新创建，保留 ref 和配置", code="pull_state_changed")
    if remaining.returncode != 1:
        raise MDFError("无法核验源分支删除结果，保留现场", code="command_failed")
    section = git(primary, "config", "--local", "--get-regexp", rf"^branch\.{re.escape(source)}\.", check=False)
    if section.returncode == 0:
        git(primary, "config", "--local", "--remove-section", f"branch.{source}")
    elif section.returncode != 1:
        raise MDFError("无法读取已删除分支的配置，保留现场", code="command_failed")


def confirm_pull(state, pull):
    """只以平台事实确认候选提交；push 响应丢失时仍可恢复。"""
    if pull is None:
        return
    if pull["source"] != state["source"] or pull["target"] != state["target"]:
        raise MDFError("PR/MR 的来源或目标已变化", code="pull_state_changed")
    pending = state.get("pending_head")
    if pending and pull["head"] == pending:
        state["head"] = pending
        state.pop("pending_head")
    elif pull["head"] != state["head"]:
        raise MDFError("PR/MR 的源提交与恢复记录不符", code="pull_state_changed")


def check_source(repo, state):
    """发布或清理前核对源现场，不先产生 tag 或回合副作用。"""
    occupant = worktree_map(repo).get(state["source"])
    if occupant is not None:
        ensure_clean(occupant)
    current = git(repo, "rev-parse", "--verify", f"refs/heads/{state['source']}", check=False)
    if (not current.returncode and current.stdout.strip() != state["head"]) or state.get("pending_head"):
        raise MDFError("已合并 PR/MR 之外仍有源提交，保留现场", code="pull_state_changed")


@contextmanager
def finish_lock(repo):
    """锁住同一 Git common dir 的 PR 收口；进程退出时由 OS 自动释放。"""
    path = state_path(repo, "closeout").parent / ".pr-closeout.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        try:
            if os.name == "nt":
                import msvcrt
                if path.stat().st_size == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise MDFError("另一个 PR close-out 或 sync 正在操作此仓库，请稍后重试", code="finish_busy") from exc
        yield


def finish(repo, source, settings, *, phase="close-out"):
    with finish_lock(repo):
        _finish(repo, source, settings, phase=phase)


def _finish(repo, source, settings, *, phase):
    if branch_details(source)["kind"] == "adhoc":
        from mdf_core.lifecycle.adhoc_context import require_source
        require_source(source)
    path = state_path(repo, source)
    state = read_json(path) if path.exists() else None
    identity = origin(repo, settings["provider"])
    forge = Forge(repo, identity)
    details = branch_details(source)
    target = "master" if details["kind"] in {"release", "hotfix"} else "develop"
    if state and (state.get("mode") != "pr" or state.get("identity") != identity
                  or state.get("source") != source or state.get("target") != target):
        raise MDFError("PR/MR 恢复记录与当前配置不符", code="pull_state_changed")
    from mdf_core.workspace.squash import require_ready
    if state is None and details["kind"] == "adhoc":
        from mdf_core.lifecycle.adhoc_context import material
        from mdf_core.lifecycle.adhoc import completion
        work = worktree_map(repo).get(source, repo)
        _, ledger = material(work, source)
        if not ledger:
            git(repo, "fetch", "origin", "--prune")
            existing = forge.find(source, target)
            if existing and existing["state"] == "merged":
                ensure_clean(work)
                if sha(work, "HEAD") != existing["head"]:
                    raise MDFError("接管已合并 PR 须绑定原 source tip", code="pull_state_changed")
                completion(work, source)
                merged = verified_merge(repo, existing, source, target, existing["head"])
                state = {"mode": "pr", "identity": identity, "source": source, "target": target,
                         "head": existing["head"], "pull": existing, "completed": False,
                         "merge_commit": merged, "retained_worktree": str(work)}
                write_json(path, state)
            elif ancestor(repo, sha(repo, source), sha(repo, f"origin/{target}")):
                raise MDFError("没有未合入提交；不创建 PR 或删除分支", code="no_pending_commits")
    if state is None and phase == "close-out":
        raise MDFError("先完成 pr intent，再执行 close-out", code="pr_not_merged")
    if state is None:
        preflight(repo, source)
        require_ready(repo, source)
        state = {"mode": "pr", "identity": identity, "source": source, "target": target,
                 "head": sha(repo, source), "pull": None, "completed": False,
                 "retained_worktree": str(worktree_map(repo).get(source, repo))}
        write_json(path, state)
    git(repo, "fetch", "origin", "--prune")
    pull = forge.get(state["pull"]["id"]) if state.get("pull") else forge.find(source, target)
    confirm_pull(state, pull)
    write_json(path, state)
    if phase == "close-out" and (pull is None or pull["state"] != "merged"):
        raise MDFError("PR/MR 尚未 merged；由 pr intent 继续推进", code="pr_not_merged")
    if pull is None or pull["state"] == "open":
        current = git(repo, "rev-parse", "--verify", f"refs/heads/{source}", check=False)
        if current.returncode:
            raise MDFError("未合并的源分支不存在", code="missing_branch")
        head = current.stdout.strip()
        if head != state["head"] or state.get("pending_head"):
            if not ancestor(repo, state.get("pending_head", state["head"]), head):
                raise MDFError("源分支历史已改写", code="pull_state_changed")
            preflight(repo, source)
            require_ready(repo, source)
            state["pending_head"] = sha(repo, source)
            write_json(path, state)
        # 非 force 精确推送本次源提交；重复 push 为 noop。
        require_ready(repo, source)
        pushed_head = state.get("pending_head", state["head"])
        git(repo, "push", "--no-follow-tags", "origin", f"{pushed_head}:refs/heads/{source}")
        if pull is None:
            pull = forge.create(source, target, f"chore(delivery): 合入 {source}",
                                "MDF 交付；请使用 merge commit。合并后再次执行 $mdf close-out 续办。")
        else:
            pull = forge.get(pull["id"])
    confirm_pull(state, pull)
    write_json(path, state)
    if pull["source"] != source or pull["target"] != target or pull["head"] != state["head"]:
        raise MDFError("PR/MR 与已准备交付不一致", code="pull_state_changed")
    state["pull"] = pull
    write_json(path, state)
    status = "waiting_for_merge" if pull["state"] == "open" else "closed_without_merge"
    if pull["state"] == "merged":
        check_source(repo, state)
        git(repo, "fetch", "origin", "--prune")
        merged = verified_merge(repo, pull, source, target, state["head"])
        if state.get("merge_commit") not in (None, merged):
            raise MDFError("平台合并结果已变化", code="pull_state_changed")
        state["merge_commit"] = merged
        write_json(path, state)
        if phase == "pr":
            emit({"ok": True, "operation": "pr", "mode": "pr", "source": source,
                  "completed": True, "status": "merged", "pull_request": pull,
                  "merge_commit": merged, "next_intent": "close-out"})
            return
        for branch in (["master", "develop"] if target == "master" else ["develop"]):
            occupant = worktree_map(repo).get(branch)
            if occupant:
                ensure_clean(occupant)
        sync_local(repo, target, integrate_develop=True)
        ready = True
        if target == "master":
            from mdf_core.lifecycle.pull_publish import publish
            ready = publish(repo, state, details["version"], path)
        if ready:
            cleanup_remote(repo, state, path)
            cleanup(repo, state)
            state["completed"] = True
            status = "completed"
        else:
            status = "published_pending_backmerge"
        write_json(path, state)
    emit({"ok": True, "operation": "pr" if phase == "pr" else "finish-gitflow", "mode": "pr", "source": source,
          "completed": state["completed"], "status": status, "pull_request": pull,
          "merge_commit": state.get("merge_commit"), "backmerge": state.get("backmerge"),
          "tag": state.get("tag"), "targets": [target] + (["develop"] if target == "master" else []),
          "remote_deleted": (state.get("remote_cleanup") or {}).get("status") == "deleted",
          "deleted": source if state["completed"] else None, "pushed": True,
          "retained_worktree": state.get("retained_worktree"), "primary_worktree": str(primary_worktree(repo))})
