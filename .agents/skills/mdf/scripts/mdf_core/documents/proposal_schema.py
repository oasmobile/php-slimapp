"""Proposal 的阶段、拒绝原因与替代关系。"""
from mdf_core.foundation.constants import OBJECT_ID_RE
from mdf_core.foundation.errors import add_finding
from mdf_core.foundation.textutil import stable_semver


def validate_proposal_fields(metadata, rel, findings):
    status = metadata.get("status")
    allowed = {"id", "type", "status", "depends_on", "reject-reason",
               "duplicate_of", "replaced_by", "released_in", "milestone"}
    for key in sorted(set(metadata) - allowed):
        add_finding(findings, "proposal.field", f"不支持的 Proposal 字段: {key}", rel)
    if "milestone" in metadata:
        milestone = metadata["milestone"]
        if not isinstance(milestone, str) or not milestone.strip():
            add_finding(findings, "proposal.milestone",
                        "milestone 必须为非空字符串；无归属时省略字段", rel)
        elif OBJECT_ID_RE.fullmatch(milestone):
            add_finding(findings, "proposal.milestone", "milestone 不得与对象 ID 同形", rel)
    version = metadata.get("released_in")
    if status == "released":
        if stable_semver(version) is None:
            add_finding(findings, "proposal.released_in", "released 必须有稳定发布版本", rel)
    elif version is not None:
        add_finding(findings, "proposal.released_in", "仅 released 可声明发布版本", rel)
    reason = metadata.get("reject-reason")
    if status == "rejected":
        if reason not in {"wont-do", "obsolete", "duplicate"}:
            add_finding(findings, "proposal.reject_reason", "rejected 需要拒绝原因", rel)
    elif reason is not None:
        add_finding(findings, "proposal.reject_reason", "仅 rejected 可声明拒绝原因", rel)
    duplicate = metadata.get("duplicate_of")
    if status == "rejected" and reason == "duplicate":
        if not isinstance(duplicate, str) or not duplicate.startswith("prp-"):
            add_finding(findings, "proposal.duplicate_of", "duplicate 需要 canonical PRP ID", rel)
    elif duplicate is not None:
        add_finding(findings, "proposal.duplicate_of", "仅 duplicate 可声明重复对象", rel)
    replacements = metadata.get("replaced_by")
    if status == "replaced":
        if (not isinstance(replacements, list) or len(replacements) < 2
                or any(not isinstance(item, str) for item in replacements)
                or len(set(map(str, replacements))) != len(replacements)):
            add_finding(findings, "proposal.replaced_by", "replaced 需要至少两个不同替代 ID", rel)
    elif replacements is not None:
        add_finding(findings, "proposal.replaced_by", "仅 replaced 可声明替代对象", rel)
