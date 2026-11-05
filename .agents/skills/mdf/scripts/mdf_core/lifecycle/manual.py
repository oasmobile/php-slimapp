"""人工 feature 的固定 objectives 清单。"""
import re

from mdf_core.foundation.errors import MDFError

STEPS = ("start", "人工工作", "lint", "code-review", "verify smoke", "fact update", "close-out")


def require_manual_objectives(text, *, starting=False, finishing=False, pr_mode=False):
    steps = (*STEPS[:-1], "pr") if pr_mode else STEPS
    items = re.findall(r"(?m)^- \[([ x])\] (.+?)\s*$", text)
    if tuple(name for _, name in items) != steps:
        raise MDFError("人工 feature 必须按配置对应的固定顺序填写步骤", code="invalid_manual_objectives")
    checked = tuple(mark == "x" for mark, _ in items)
    if starting and checked != (True, False, False, False, False, False, False):
        raise MDFError("start 仅勾选 start，人工工作必须由用户显式勾选", code="invalid_manual_objectives")
    if finishing and not all(checked):
        raise MDFError("人工 feature 尚有未完成步骤", code="manual_work_pending")


def feature_completion(repo, source, *, allow_candidate=False):
    """验证 feature Change，返回合入时的 PRP 更新与 roster。"""
    from mdf_core.lifecycle.delivery_state import locate, require_finish, git
    from mdf_core.documents.proposals import records
    from mdf_core.documents.html_documents import update_metadata
    from mdf_core.foundation.yamlutil import read_frontmatter

    root, data = locate(repo)
    require_finish(repo, root, data)
    change = root / "CHANGE.md"
    if not change.is_file():
        raise MDFError("finish 前必须补齐 Change", code="missing_change")
    meta, _ = read_frontmatter(change)
    if data.get("manual"):
        from mdf_core.workspace.merge_policy import configured
        require_manual_objectives((root / "objectives.md").read_text(), finishing=True,
                                  pr_mode=configured(repo)["mode"] == "pr")
        if meta.get("proposals") != [] or meta.get("source_branch") != source:
            raise MDFError("人工 feature 的 Change 不引用 PRP", code="invalid_change")
        return None, data["roster"]
    if meta.get("proposals") != [data["proposal"]] or meta.get("source_branch") != source:
        raise MDFError("Change 必须对应本 feature 的唯一 PRP", code="invalid_change")
    path, proposal, _ = records(repo)[data["proposal"]]
    candidate = allow_candidate and proposal["status"] == "implemented"
    if proposal["status"] != "ready" and not candidate:
        raise MDFError("交付 PRP 状态不正确", code="invalid_proposal")
    proposal_rel = path.relative_to(repo)

    def complete_feature(merge_repo):
        target_path = merge_repo / proposal_rel
        merged, body = read_frontmatter(target_path)
        target_path.write_text(update_metadata(target_path.read_text(), {**merged, "status": "implemented"}))
        git(merge_repo, "add", "--", str(proposal_rel))

    return complete_feature, data["roster"]
