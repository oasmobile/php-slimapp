"""Adhoc 的固定 objectives 与无 PRP 收口。"""
import re
from pathlib import Path

from mdf_core.foundation.errors import MDFError

STEPS = ("工作", "lint", "code-review", "verify smart", "fact audit/update", "close-out")


def validate_start(args):
    if args.kind != "adhoc" and getattr(args, "work", None) is not None:
        raise MDFError("--work 仅用于 adhoc", code="unexpected_work")


def objectives():
    return (Path(__file__).resolve().parents[3] / "assets/templates/adhoc-objectives.md").read_text(
        encoding="utf-8"
    )


def prepare(args):
    from mdf_core.foundation.textutil import slugify

    if args.proposal or args.bug or args.version or args.objectives_file:
        raise MDFError("adhoc 不绑定对象或版本，objectives 自动生成", code="invalid_adhoc")
    if not args.name or not args.name.strip():
        raise MDFError("adhoc 需要 Agent 选定的 --name", code="invalid_slug")
    if not args.work or not args.work.strip():
        raise MDFError("adhoc 需要非空 --work 工作描述", code="missing_adhoc_work")
    if (args.roster not in (None, "solo") or args.qa not in (None, 0)
            or args.dev not in (None, 0) or args.reviewers not in (None, 1)):
        raise MDFError("adhoc 的 roster 固定为 0,0,1", code="invalid_adhoc")
    text = objectives()
    require_objectives(text, starting=True)
    return slugify(args.name), text


def require_objectives(text, *, starting=False, finishing=False, pr_mode=False):
    steps = (*STEPS[:-1], "pr") if pr_mode else STEPS
    items = re.findall(r"(?m)^- \[([ x])\] (.+?)\s*$", text)
    if tuple(name for _, name in items) != steps:
        raise MDFError("adhoc 必须按配置对应的固定顺序填写步骤", code="invalid_adhoc_objectives")
    checked = [mark == "x" for mark, _ in items]
    if starting and any(checked):
        raise MDFError("adhoc 启动时六项步骤均须未勾选", code="invalid_adhoc_objectives")
    if any(checked[index] and not checked[index - 1] for index in range(1, len(checked))):
        raise MDFError("adhoc 步骤须顺序完成，返工须退勾后续项", code="invalid_adhoc_objectives")
    if finishing and not all(checked):
        raise MDFError("adhoc 尚有未完成步骤", code="adhoc_work_pending")
    return next((step for step, done in zip(steps, checked) if not done), None)


def require_identity(data):
    from mdf_core.workspace.gitutil import branch_details

    work = data.get("work")
    roster = data["roster"]
    if (not isinstance(work, str) or not work.strip() or data["needs_design"]
            or data.get("proposal") or data.get("bug") or data.get("manual")
            or branch_details(data["branch"])["kind"] != "adhoc"
            or tuple(roster[key] for key in ("qa", "dev", "reviewers")) != (0, 0, 1)):
        raise MDFError("adhoc 身份需要工作描述、固定 solo 且不绑定对象或 design", code="invalid_delivery")


def merged_commit(repo, head):
    from mdf_core.lifecycle.delivery_state import git

    merges = git(repo, "rev-list", "--parents", "--merges", "--first-parent", "refs/heads/develop")
    for line in merges.stdout.splitlines():
        fields = line.split()
        if head in fields[2:]:
            return fields[0]
    return None


def command_status(args):
    """从原有材料与 Git 核对进度；detached 时须显式指定已知 slug。"""
    from mdf_core.lifecycle.delivery_state import git, locate, safe
    from mdf_core.foundation.errors import emit
    from mdf_core.workspace.gitutil import (
        ensure_clean,
        primary_worktree,
        repo_path,
        require_git_root,
    )
    from mdf_core.foundation.textutil import slugify

    repo = repo_path(args.repo)
    require_git_root(repo)
    if args.slug is not None and (not args.slug or slugify(args.slug) != args.slug):
        raise MDFError("材料 slug 必须为 kebab slug", code="invalid_slug")
    branch = git(repo, "branch", "--show-current").stdout.strip()
    from mdf_core.lifecycle.adhoc_context import material, require_source
    source = getattr(args, "source", None) or branch
    if not source and args.slug:
        root = safe(repo, repo / "changes/unreleased" / args.slug)
        from mdf_core.lifecycle.delivery_state import read_json
        if (root / "delivery.json").is_file():
            source = read_json(safe(repo, root / "delivery.json")).get("branch")
        elif (root / "CHANGE.md").is_file():
            from mdf_core.foundation.yamlutil import read_frontmatter
            source = read_frontmatter(safe(repo, root / "CHANGE.md"))[0].get("source_branch")
    if not source:
        raise MDFError("adhoc-status 需要当前 adhoc 或上下文已知的 --slug / --source", code="invalid_slug")
    require_source(source)
    root, ledger = material(repo, source, args.slug)
    if not ledger:
        from mdf_core.lifecycle.adhoc_finish import status
        emit({"ok": True, "operation": "adhoc-status", "result": status(repo, source, args.slug)})
        return
    slug = args.slug
    if slug is None:
        slug = root.name
    if not slug or slugify(slug) != slug:
        raise MDFError("adhoc-status 需要当前 adhoc 或上下文已知的 --slug", code="invalid_slug")
    owner = source
    if branch and branch != owner:
        raise MDFError("adhoc-status 必须绑定本次 owner worktree", code="stage_branch")
    root, data = locate(repo, slug, owner=owner)
    try:
        text = safe(repo, root / "objectives.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise MDFError("adhoc objectives 缺失或不可读", code="invalid_adhoc_objectives") from exc
    from mdf_core.workspace.merge_policy import configured
    pr_mode = configured(repo)["mode"] == "pr"
    pending = require_objectives(text, pr_mode=pr_mode)
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    merge_commit = merged_commit(repo, head)
    if merge_commit and pending is not None:
        raise MDFError("已合并的 adhoc 账本仍有未完成项，保留现场", code="invalid_delivery")
    next_step = pending or "close-out"
    state = {}
    if pr_mode:
        from mdf_core.lifecycle.publish import state_path
        from mdf_core.lifecycle.delivery_state import read_json
        path = state_path(repo, owner)
        state = read_json(path) if path.exists() else {}
        if state and (state.get("mode") != "pr" or state.get("source") != owner
                      or state.get("target") != "develop"):
            raise MDFError("PR 操作记录与 adhoc 身份不符", code="pull_state_changed")
        if state.get("merge_commit") and state.get("head") != head:
            raise MDFError("已合并 PR 之外仍有源提交", code="pull_state_changed")
        # 候选勾选不是合并证据；只有 pr 已核验并记录实际 M 后才交接收尾。
        if pending is None:
            next_step = "close-out" if state.get("merge_commit") else "pr"
    if not branch:
        ensure_clean(repo)
        source_exists = not git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{owner}",
                                check=False).returncode
        if pending is not None or source_exists or merge_commit is None:
            raise MDFError("缺少 adhoc 实际收口证据，保留现场", code="adhoc_not_finished")
        if pr_mode and (state.get("completed") is not True or state.get("merge_commit") != merge_commit
                        or (state.get("remote_cleanup") or {}).get("status") != "deleted"):
            raise MDFError("PR 收口尚未核验完成，按原 source 续办 close-out", code="adhoc_not_finished")
    emit({"ok": True, "operation": "adhoc-status", "result": {
        "material_mode": "ledger", "source": owner,
        "delivery": data, "path": str(root.relative_to(repo)), "head": head,
        "next_step": next_step if branch else None,
        "completed": not branch, "merge_commit": merge_commit,
        "owner_worktree": str(repo), "primary_worktree": str(primary_worktree(repo)),
    }})


def completion(repo, source):
    from mdf_core.lifecycle.delivery_state import locate, require_finish
    from mdf_core.foundation.yamlutil import read_frontmatter

    from mdf_core.lifecycle.adhoc_context import material, complete_change
    root, ledger = material(repo, source)
    if not ledger:
        return complete_change(repo, source, root)
    root, data = locate(repo, root.name, owner=source)
    require_finish(repo, root, data)
    from mdf_core.workspace.merge_policy import configured
    require_objectives((root / "objectives.md").read_text(encoding="utf-8"), finishing=True,
                       pr_mode=configured(repo)["mode"] == "pr")
    change = root / "CHANGE.md"
    if not change.is_file():
        raise MDFError("finish 前必须补齐 Change", code="missing_change")
    meta, _ = read_frontmatter(change)
    if (meta.get("change_kind") not in {"adhoc", "fix"} or meta.get("proposals") != []
            or meta.get("source_branch") != source):
        raise MDFError("adhoc 的 Change 必须对应源分支且不引用 PRP", code="invalid_change")
    return data["roster"]
