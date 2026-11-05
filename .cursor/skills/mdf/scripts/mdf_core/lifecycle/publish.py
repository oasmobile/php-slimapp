"""记录并核验发布的部分成功状态，恢复时不重做已完成的合并或 tag。"""
from pathlib import Path

from mdf_core.lifecycle.delivery_state import read_json, safe, write_json
from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import current_branch, ensure_clean, primary_worktree, worktree_map


def state_path(repo, source):
    from mdf_core.workspace.gitflow import _git
    common = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    from mdf_core.workspace.gitutil import branch_details
    if branch_details(source)["kind"] == "adhoc":
        import hashlib
        return safe(common, common / "mdf/finish" / f"adhoc-{hashlib.sha256(source.encode()).hexdigest()}.json")
    return safe(common, common / "mdf/finish" / f"{source}.json")


def publish(repo, source, version):
    from mdf_core.workspace.gitflow import _git, _exists, _merge, _synced
    primary = primary_worktree(repo)
    path = state_path(repo, source)
    state = read_json(path) if path.exists() else None
    tag = f"v{version}"
    source_ref = f"refs/heads/{source}"
    head = _git(repo, "rev-parse", "--verify", source_ref, check=False)
    if state is None:
        if head.returncode:
            raise MDFError("发布源分支不存在", code="missing_branch")
        _synced(repo, "master")
        remote_tag = _git(repo, "ls-remote", "--tags", "origin", f"refs/tags/{tag}").stdout
        if _exists(repo, f"refs/tags/{tag}") or remote_tag.strip():
            raise MDFError("版本 tag 已存在", code="tag_exists")
        state = {"source": source, "head": head.stdout.strip(), "tag": tag,
                 "origin": _git(repo, "remote", "get-url", "origin").stdout.strip(),
                 "before": {target: _git(repo, "rev-parse", target).stdout.strip()
                            for target in ("master", "develop")}, "merged": {}, "pushed": False}
        write_json(path, state)
    elif (state.get("source") != source or state.get("tag") != tag
          or state.get("origin") != _git(repo, "remote", "get-url", "origin").stdout.strip()
          or (not head.returncode and head.stdout.strip() != state.get("head"))
          or (head.returncode and not state.get("pushed"))):
        raise MDFError("发布现场与恢复记录不一致", code="publish_state_changed")

    for target in ("master", "develop"):
        incoming = state["head"] if target == "master" else state["merged"]["master"]
        before = state["before"][target]
        current = _git(repo, "rev-parse", target).stdout.strip()
        remote = _git(repo, "rev-parse", "origin/master").stdout.strip() if target == "master" else None
        recorded = state["merged"].get(target)
        if target == "develop" and recorded is None and current != before:
            parents = _git(repo, "show", "-s", "--format=%P", current).stdout.split()
            # 精确匹配的未记录合并仍走恢复；正常开发进度成为新的合并基线。
            if parents != [before, incoming]:
                before = current
                state["before"][target] = before
                write_json(path, state)
        if current == before and recorded is None:
            if target == "master" and remote != before:
                raise MDFError("远端分支已变化", code="publish_state_changed")
            occupant = worktree_map(primary).get(target)
            # 目标没有 checkout 时在主 worktree 合并，保留源 worktree 的分支身份。
            work = occupant if occupant is not None else primary
            ensure_clean(work)
            _merge(work, incoming, target)
            current = _git(repo, "rev-parse", target).stdout.strip()
        elif recorded is None:
            # 合并成功但写记录前中断：只接受精确的双亲合并提交。
            parents = _git(repo, "show", "-s", "--format=%P", current).stdout.split()
            if parents != [before, incoming] or (target == "master" and remote not in (before, current)):
                raise MDFError("未记录的分支变化，不能自动恢复", code="publish_state_changed")
        elif current != recorded or (target == "master" and remote not in (before, recorded)):
            raise MDFError("发布分支被其他操作改变", code="publish_state_changed")
        state["merged"][target] = current
        write_json(path, state)
        if target == "master":
            if _exists(repo, f"refs/tags/{tag}"):
                kind = _git(repo, "cat-file", "-t", f"refs/tags/{tag}").stdout.strip()
                tagged = _git(repo, "rev-parse", f"refs/tags/{tag}^{{commit}}").stdout.strip()
                if kind != "tag" or tagged != current:
                    raise MDFError("发布 tag 与已合并提交不符", code="publish_state_changed")
            else:
                shown = _git(
                    repo, "show", f"{current}:CHANGELOG.md", check=False
                )
                if shown.returncode:
                    raise MDFError(
                        "发布提交缺少 CHANGELOG.md，不能创建发布 tag",
                        code="missing_changelog",
                    )
                from mdf_core.lifecycle.closeout_render import changelog_excerpt, release_tag_message
                message = release_tag_message(
                    tag, changelog_excerpt(shown.stdout, version)
                )
                # verbatim：默认 strip 会丢掉 CHANGELOG 里以 # 开头的标题行。
                _git(
                    repo,
                    "tag",
                    "-a",
                    tag,
                    current,
                    "--cleanup=verbatim",
                    "-m",
                    message,
                )

    remote_refs = dict(line.split()[::-1] for line in _git(
        repo, "ls-remote", "origin", "refs/heads/master",
        f"refs/tags/{tag}").stdout.splitlines())
    tag_object = _git(repo, "rev-parse", f"refs/tags/{tag}").stdout.strip()
    expected = {"refs/heads/master": state["merged"]["master"], f"refs/tags/{tag}": tag_object}
    if remote_refs != expected:
        if (remote_refs.get(f"refs/tags/{tag}") not in (None, tag_object)
                or remote_refs.get("refs/heads/master") not in
                (state["before"]["master"], state["merged"]["master"])):
            raise MDFError("远端发布状态有冲突", code="publish_state_changed")
        _git(primary, "push", "--atomic", "origin", "master", f"refs/tags/{tag}")
    state["pushed"] = True
    write_json(path, state)
    return state
