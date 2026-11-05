"""PR 发布后的固定 tag 和可恢复 develop 回合。"""
from mdf_core.foundation.errors import MDFError
from mdf_core.lifecycle.delivery_state import write_json
from mdf_core.workspace.gitutil import add_linked_worktree, ensure_clean, git_in_progress_head, sibling_worktree, worktree_map
from mdf_core.workspace.merge_policy import ancestor, git, sha


def tag_release(repo, state, version, path):
    tag, merged = f"v{version}", state["merge_commit"]
    ref = f"refs/tags/{tag}"
    local = git(repo, "rev-parse", "--verify", ref, check=False)
    if local.returncode:
        from mdf_core.lifecycle.closeout_render import changelog_excerpt, release_tag_message
        changelog = git(repo, "show", f"{merged}:CHANGELOG.md").stdout
        message = release_tag_message(tag, changelog_excerpt(changelog, version))
        git(repo, "tag", "-a", tag, merged, "--cleanup=verbatim", "-m", message)
    if (git(repo, "cat-file", "-t", ref).stdout.strip() != "tag" or sha(repo, ref) != merged):
        raise MDFError("现有 tag 与固定发布提交不符", code="tag_conflict")
    expected = git(repo, "rev-parse", ref).stdout.strip()
    remote = git(repo, "ls-remote", "origin", ref).stdout.split()
    if remote and remote[0] != expected:
        raise MDFError("远端 tag 与本次发布不符", code="tag_conflict")
    if not remote:
        git(repo, "push", "--no-follow-tags", "origin", f"{ref}:{ref}")
    state["tag"] = tag
    write_json(path, state)


def publish(repo, state, version, path):
    from mdf_core.lifecycle.pull_finish import sync_local
    tag_release(repo, state, version, path)
    merged = state["merge_commit"]
    git(repo, "fetch", "origin", "--prune")
    remote = "refs/remotes/origin/develop"
    record = state.get("backmerge")
    if state.get("completed") or state.get("publication_completed"):
        if not ancestor(repo, merged, remote) or (record and not ancestor(repo, record["head"], remote)):
            raise MDFError("已完成回合的远端历史已变化，保留现场", code="pull_state_changed")
        sync_local(repo, "develop", integrate_develop=True)
        return True
    if ancestor(repo, merged, remote) and (record is None or (
            record.get("head") and ancestor(repo, record["head"], remote))):
        state["publication_completed"] = True
        write_json(path, state)
        sync_local(repo, "develop", integrate_develop=True)
        return True
    sync_local(repo, "develop", integrate_develop=True)
    if record is None:
        branch = f"codex/backmerge/{version}"
        work = sibling_worktree(repo, branch)
        record = {"source": branch, "worktree": str(work), "base": sha(repo, remote)}
        if work.exists() or not git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode:
            raise MDFError("回合分支或 worktree 已存在", code="collision")
        state["backmerge"] = record
        write_json(path, state)
    from pathlib import Path
    work = Path(record["worktree"])
    occupant = worktree_map(repo).get(record["source"])
    if occupant is None and not work.exists():
        branch = git(repo, "rev-parse", "--verify", f"refs/heads/{record['source']}", check=False)
        if branch.returncode:
            if record.get("head"):
                raise MDFError("已记录的回合分支丢失，保留现场", code="pull_state_changed")
            add_linked_worktree(repo, record["source"], work, record["base"])
        elif branch.stdout.strip() == record.get("head", record["base"]):
            work.parent.mkdir(parents=True, exist_ok=True)
            git(repo, "worktree", "add", str(work), record["source"])
        else:
            raise MDFError("回合分支与恢复记录不符，保留现场", code="pull_state_changed")
    elif occupant != work:
        raise MDFError("回合 worktree 与记录不符", code="pull_state_changed")
    if git_in_progress_head(work):
        return False
    ensure_clean(work)
    previous_head = record.get("head")
    if previous_head and not ancestor(repo, previous_head, sha(work, "HEAD")):
        raise MDFError("回合分支历史已改写，保留现场", code="pull_state_changed")
    from mdf_core.workspace.squash import require_ready
    if not ancestor(repo, merged, "refs/heads/" + record["source"]):
        require_ready(work)
        result = git(work, "merge", "--no-ff", "--no-commit", merged, check=False)
        if result.returncode:
            record["conflicts"] = git(work, "diff", "--name-only", "--diff-filter=U").stdout.splitlines()
            write_json(path, state)
            if git_in_progress_head(work):
                return False
            raise MDFError("无法开始回合 merge，保留现场", code="backmerge_failed")
        git(work, "commit", "-m", f"chore(release): 合回 {version} 到 develop")
    require_ready(work)
    head = sha(work, "HEAD")
    record["head"] = head
    write_json(path, state)
    result = git(work, "push", "--no-follow-tags", "origin", f"{head}:refs/heads/develop", check=False)
    git(repo, "fetch", "origin", "--prune")
    if ancestor(repo, merged, remote) and ancestor(repo, head, remote):
        record.pop("push_error", None)
        record.pop("conflicts", None)
        state["publication_completed"] = True
        write_json(path, state)
        sync_local(repo, "develop", integrate_develop=True)
        return True
    record["push_error"] = result.stderr.strip() or "远端 develop 尚未包含回合提交"
    write_json(path, state)
    return False
