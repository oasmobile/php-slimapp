"""Proposal 身份、依赖图和未开工判定。"""
import json
from pathlib import Path

from mdf_core.foundation.constants import OBJECT_FILE_RE, PRP_ID_RE
from mdf_core.foundation.errors import MDFError, serialize_findings
from mdf_core.workspace.gitutil import run
from mdf_core.foundation.textutil import new_prp_id
from mdf_core.inspection.validate_objects import iter_object_files, validate_object
from mdf_core.inspection.validate_records import unsatisfied_depends_on, validate_record_references
from mdf_core.foundation.yamlutil import read_frontmatter


def proposal_slug_on_ref(repo, identifier, ref):
    listed = run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", "docs/proposals"],
        cwd=repo,
    )
    found = []
    for rel in listed.stdout.splitlines():
        parts = Path(rel).parts
        if len(parts) != 3 or parts[:2] != ("docs", "proposals"):
            continue
        match = OBJECT_FILE_RE.fullmatch(parts[2])
        if match and match.group(1) == identifier:
            found.append(match.group(2))
    if not found:
        raise MDFError("缺少指定 PRP", code="missing_proposal")
    if len(found) > 1:
        raise MDFError("Proposal ID 重复", code="invalid_proposals")
    return found[0]


def new_prp_ids(repo: Path, count: int) -> list[str]:
    used = set()
    for path in iter_object_files(repo, "proposal"):
        match = OBJECT_FILE_RE.fullmatch(path.name)
        if match and PRP_ID_RE.fullmatch(match.group(1)):
            used.add(match.group(1))
    # 100 个数字前缀 ×（100 个纯数字后缀 + 2 × 24 × 10 个单字母后缀）。
    if sum(len(identifier) == 8 for identifier in used) + count > 58000:
        raise MDFError("PRP ID 空间不足", code="prp_id_exhausted")
    identifiers = []
    while len(identifiers) < count:
        identifier = new_prp_id()
        if identifier not in used:
            used.add(identifier)
            identifiers.append(identifier)
    return identifiers


def records(repo):
    result = {}
    for path in iter_object_files(repo, "proposal"):
        meta, body = read_frontmatter(path)
        if meta.get("id") in result:
            raise MDFError("Proposal ID 重复", code="invalid_proposals")
        result[meta.get("id")] = (path, meta, body)
    return result


def check_proposals(repo):
    findings = []
    for path in iter_object_files(repo, "proposal"):
        validate_object(repo, path, "proposal", findings)
    validate_record_references(repo, findings)
    if findings:
        raise MDFError("Proposal 契约或依赖图无效", code="invalid_proposals",
                       details={"findings": serialize_findings(findings)})
    return records(repo)


def started_ids(repo):
    """收集当前工作区与全部 feature 分支的开工记录所指向的 Proposal ID。"""
    found = set()
    root = repo / "changes"
    if root.exists():
        for path in root.rglob("delivery.json"):
            if path.is_symlink():
                raise MDFError("工作记录不能为符号链接", code="unsafe_path")
            try:
                data = json.loads(path.read_text())
            except (ValueError, OSError) as exc:
                raise MDFError("工作记录损坏", code="invalid_delivery") from exc
            if not isinstance(data, dict):
                raise MDFError("工作记录必须是 JSON 对象", code="invalid_delivery")
            if isinstance(data.get("proposal"), str):
                found.add(data["proposal"])
    refs = run(["git", "for-each-ref", "--format=%(refname)",
                "refs/heads/feature/", "refs/remotes/origin/feature/"], cwd=repo).stdout.splitlines()
    for ref in refs:
        paths = run(["git", "ls-tree", "-r", "--name-only", ref, "--", "changes"],
                    cwd=repo).stdout.splitlines()
        for path in paths:
            if not path.endswith("/delivery.json"):
                continue
            raw = run(["git", "show", f"{ref}:{path}"], cwd=repo).stdout
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise MDFError("分支工作记录必须是 JSON 对象", code="invalid_delivery")
                if isinstance(data.get("proposal"), str):
                    found.add(data["proposal"])
            except ValueError as exc:
                raise MDFError("关联分支的工作记录损坏", code="invalid_delivery") from exc
    return found


def started(repo, identifier):
    return identifier in started_ids(repo)


def require_startable(repo, identifier):
    from mdf_core.foundation.paths import load_manifest
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("start 需要 ready 仓库", code="manifest_not_ready")
    objects = check_proposals(repo)
    if identifier not in objects:
        raise MDFError("缺少指定 PRP", code="missing_proposal")
    path, meta, _ = objects[identifier]
    if meta["status"] != "ready" or len(path.relative_to(repo / "docs").parts) != 2:
        raise MDFError("feature 需要 active ready PRP", code="proposal_not_ready")
    metas = {key: value[1] for key, value in objects.items()}
    blocked = unsatisfied_depends_on(meta["depends_on"], metas)
    if blocked:
        raise MDFError("PRP 依赖尚未满足", code="proposal_blocked", details={"blocked_by": blocked})
    if started(repo, identifier):
        raise MDFError("PRP 已开工", code="proposal_started")
    return path
