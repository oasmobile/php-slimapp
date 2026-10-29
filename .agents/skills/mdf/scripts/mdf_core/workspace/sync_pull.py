"""sync 的 PR/MR 计划、持久化提交与同名 ff 恢复。"""
from uuid import uuid4

from mdf_core.foundation.errors import MDFError
from mdf_core.integrations.forge import Forge, origin
from mdf_core.lifecycle.delivery_state import read_json, write_json
from mdf_core.lifecycle.publish import state_path
from mdf_core.lifecycle.pull_finish import remote_source_head, sync_local, verified_merge
from mdf_core.workspace.gitutil import ensure_clean, worktree_map
from mdf_core.workspace.merge_policy import ancestor, configured, git, sha


def settings(repo):
    candidates = [configured(repo)]
    for branch in ("master", "develop"):
        ref = f"refs/remotes/origin/{branch}"
        if not git(repo, "cat-file", "-e", f"{ref}:.mdf/manifest.yaml", check=False).returncode:
            candidates.append(configured(repo, ref))
    providers = {item["provider"] for item in candidates if item["mode"] == "pr"}
    if len(providers) > 1:
        raise MDFError("PR mode 的 provider 不一致", code="invalid_closeout")
    return {"mode": "pr", "provider": providers.pop()} if providers else {"mode": "local"}


def plans(repo, branches):
    """预览仅查询 Git 和恢复记录；不调用平台或写入。"""
    from mdf_core.inspection.push_audit import audit
    config = settings(repo)
    result = {}
    from mdf_core.workspace.dev_pr import pending
    from mdf_core.workspace.merge_policy import trivial_commits
    dev = pending(repo)
    for branch in ("master", "develop"):
        if branch == "develop" and dev:
            result[branch] = {"action": "dev_pr", "record": dev}
            continue
        path = state_path(repo, f"sync/{branch}")
        state = read_json(path) if branch == "master" and path.exists() else None
        if state and not state.get("completed"):
            source = git(repo, "rev-parse", "--verify", f"refs/heads/{state['source']}", check=False)
            result[branch] = {"action": "resume_pr", "record": state,
                              "source_head": source.stdout.strip() if not source.returncode else state["source_head"]}
            continue
        if config["mode"] != "pr":
            continue
        info = branches[branch]
        report = None
        if branch == "develop" and info["relation"] == "ahead":
            if trivial_commits(repo, info["remote"], info["local"]):
                continue
        if info["relation"] == "ahead":
            evidence = {"sources": {name: sha(repo, f"refs/heads/{name}") for name in ("master", "planning")},
                        "pull_requests": []}
            report = audit(repo, branch, info["remote"], info["local"], evidence, source_prefix="refs/heads")
            if report["verdict"] == "pass" and report.get("reason") != "local_mode":
                continue
        elif info["relation"] != "diverged":
            continue
        result[branch] = {"action": "dev_pr" if branch == "develop" else "create_pr", "head": info["local"], "base": info["remote"],
                          "provider": config["provider"], "audit": report}
    return result


def _changed(message):
    raise MDFError(message + "；保留现场", code="pull_state_changed")


def _validate(repo, state, branch, identity, source_head):
    if (state.get("identity") != identity or state.get("target") != branch
            or not str(state.get("source", "")).startswith(f"codex/sync/{branch}-")):
        _changed("sync PR/MR 恢复记录与目标不符")
    current = sha(repo, f"refs/heads/{branch}")
    # 只接受原 tip 或已包含它的远端历史；不吞掉等待期间的本地开发。
    if current != state["head"] and not (
            ancestor(repo, state["head"], current)
            and ancestor(repo, current, f"refs/remotes/origin/{branch}")):
        _changed(f"本地 {branch} 在 PR/MR 之外发生变化")
    source = git(repo, "rev-parse", "--verify", f"refs/heads/{state['source']}", check=False)
    if not source.returncode and source.stdout.strip() != source_head:
        _changed("sync source branch 已变化")
    if not ancestor(repo, state["source_head"], source_head):
        _changed("sync source branch 历史已改写")
    occupant = worktree_map(repo).get(state["source"])
    if occupant:
        ensure_clean(occupant)


def _pending_head(repo, state, head):
    """中断期间的平台 head 只能位于已确认 source 提交链内。"""
    return bool(head and ancestor(repo, state.get("previous_head", state["source_head"]), head)
                and ancestor(repo, head, state["source_head"]))


def _pull_matches(repo, state, pull, *, updating=False):
    matches = pull["head"] == state["source_head"]
    if updating and pull["state"] == "open":
        matches = _pending_head(repo, state, pull["head"])
    if (pull["source"] != state["source"] or pull["target"] != state["target"]
            or not matches):
        _changed("平台 PR/MR 的 source、target 或 head 已变化")


def advance(repo, plan, remote_tips):
    """保持 trunk 不动，先提交 source PR；核验平台 merge 后才 ff 本地。"""
    config = settings(repo)
    results = {}
    for branch, item in plan.items():
        if item["action"] == "dev_pr":
            from mdf_core.workspace.dev_pr import prepare
            results[branch] = prepare(repo, expected_head=item.get("head"), expected_base=item.get("base"))
            continue
        state = item.get("record")
        provider = state["identity"]["provider"] if state else item["provider"]
        if config["mode"] != "pr" or config.get("provider") != provider:
            _changed("PR mode 配置在同步期间变化")
        identity = origin(repo, provider)
        path = state_path(repo, f"sync/{branch}")
        if state is None:
            # 先落盘，再建 branch/push/create；任何响应丢失均通过同一 source 恢复。
            if path.exists():
                old = read_json(path)
                write_json(state_path(repo, f"sync/history/{old['source']}"), old)
            state = {"identity": identity, "source": f"codex/sync/{branch}-{uuid4().hex}",
                     "target": branch, "head": item["head"], "base": item["base"],
                     "source_head": item["head"], "pull": None, "completed": False}
            write_json(path, state)
        head = item.get("source_head", state["source_head"])
        _validate(repo, state, branch, identity, head)
        if head != state["source_head"]:
            state.setdefault("previous_head", state["source_head"])
            state["source_head"] = head
            write_json(path, state)
        source = state["source"]
        if git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{source}", check=False).returncode:
            git(repo, "branch", source, head)
        forge = Forge(repo, identity)
        pull = forge.get(state["pull"]["id"]) if state.get("pull") else forge.find(source, branch)
        if pull is not None:
            _pull_matches(repo, state, pull, updating=True)
        if pull is None or pull["state"] == "open":
            remote = remote_source_head(repo, source)
            if remote is not None and not _pending_head(repo, state, remote):
                _changed("远端 sync source branch 已变化")
            if pull is not None and remote is None:
                _changed("未合并 PR/MR 的远端 source 已丢失")
            if remote != head:
                git(repo, "push", "--no-follow-tags", "origin", f"{head}:refs/heads/{source}")
            if pull is None:
                pull = forge.create(source, branch, f"chore(sync): 同步本地 {branch} 增量",
                                    "MDF sync；请使用保留 source commit 的 merge commit。合并后再次执行 $mdf sync。")
            else:
                pull = forge.get(pull["id"])
            _pull_matches(repo, state, pull)
        state.pop("previous_head", None)
        state["pull"] = pull
        write_json(path, state)
        status = "waiting_for_merge" if pull["state"] == "open" else "closed_without_merge"
        if pull["state"] == "merged":
            git(repo, "fetch", "origin", "--prune")
            if any(sha(repo, f"refs/remotes/origin/{name}") != tip for name, tip in remote_tips.items()):
                from mdf_core.workspace.sync import _preview
                raise MDFError("恢复期间远端 tip 已变化，请重新确认", code="sync_plan_changed",
                               details=_preview(repo, pr=True))
            _validate(repo, state, branch, identity, head)
            merged = verified_merge(repo, pull, source, branch, head)
            if state.get("merge_commit") not in (None, merged):
                _changed("平台合并结果已变化")
            if not ancestor(repo, state["base"], merged + "^1"):
                _changed("目标分支历史已改写")
            state["merge_commit"] = merged
            write_json(path, state)
            sync_local(repo, branch)
            state["completed"] = True
            write_json(path, state)
            status = "completed"
        results[branch] = {"status": status, "pull_request": pull, "source": source,
                           "head": head, "merge_commit": state.get("merge_commit")}
    return results
