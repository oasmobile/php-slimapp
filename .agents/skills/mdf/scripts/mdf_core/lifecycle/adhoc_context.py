"""Adhoc 的真实 source、材料目录与固定改动范围；不创建交付账本。"""
import hashlib
import re

from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.yamlutil import read_frontmatter
from mdf_core.lifecycle.delivery_state import read_json, safe
from mdf_core.workspace.gitutil import branch_details
from mdf_core.workspace.merge_policy import ancestor, configured, git, sha


def require_source(source):
    from mdf_core.lifecycle.roster import parse_role_branch

    if (not isinstance(source, str) or branch_details(source)["kind"] != "adhoc" or parse_role_branch(source)
            or source.startswith("codex/backmerge/")):
        raise MDFError("需要独立 adhoc owner；角色与 backmerge 沿用所属 workflow", code="stage_branch")


def material(repo, source, slug=None):
    """优先精确身份；默认目录冲突时使用稳定 source hash，绝不覆盖别的交付。"""
    require_source(source)
    parent = safe(repo, repo / "changes/unreleased")
    default = parent / branch_details(source)["slug"]
    matches = []
    for root in sorted(parent.iterdir()) if parent.is_dir() else []:
        root = safe(repo, root)
        if not root.is_dir():
            continue
        record, change = root / "delivery.json", root / "CHANGE.md"
        if record.exists():
            try:
                identity = read_json(safe(repo, record))
            except MDFError:
                if root == default or root.name == slug:
                    raise
                continue
            if identity.get("branch") == source:
                matches.append((root, True))
        elif change.exists():
            metadata, _ = read_frontmatter(safe(repo, change))
            if metadata.get("source_branch") == source:
                matches.append((root, False))
        elif (root / "objectives.md").exists() and (root == default or root.name == slug):
            raise MDFError("已有 objectives 但交付记录缺失", code="invalid_delivery")
    if len(matches) > 1:
        raise MDFError("本 source 对应多个交付目录", code="collision")
    if matches:
        root, ledger = matches[0]
        if slug is not None and root.name != slug:
            raise MDFError("已知 slug 与本 source 材料不符", code="invalid_delivery")
        if not ledger and (root / "objectives.md").exists():
            raise MDFError("已有 objectives 但交付记录缺失", code="invalid_delivery")
        return root, ledger
    if slug is not None and slug != default.name:
        from mdf_core.foundation.textutil import slugify
        if slugify(slug) != slug:
            raise MDFError("材料 slug 必须为 kebab slug", code="invalid_slug")
        default = safe(repo, parent / slug)
    if default.exists() and any((default / name).exists() for name in ("delivery.json", "CHANGE.md")):
        suffix = hashlib.sha256(source.encode()).hexdigest()[:12]
        default = default.with_name(f"{default.name}-{suffix}")
        if default.exists() and any((default / name).exists()
                                    for name in ("delivery.json", "CHANGE.md", "objectives.md")):
            raise MDFError("Adhoc 材料目录冲突", code="collision")
    return safe(repo, default), False


def context(repo, source, slug=None, *, head=None):
    root, ledger = material(repo, source, slug)
    head = head or sha(repo, "HEAD")
    target = "refs/remotes/origin/develop" if configured(repo)["mode"] == "pr" else "refs/heads/develop"
    target_head = sha(repo, target)
    frozen = None
    if ledger:
        from mdf_core.lifecycle.delivery_state import locate
        _, data = locate(repo, root.name, owner=source)
        frozen = {"base": data["start_commit"], "source_head": head}
    elif (root / "CHANGE.md").is_file():
        metadata, _ = read_frontmatter(safe(repo, root / "CHANGE.md"))
        evidence = metadata.get("evidence")
        if isinstance(evidence, dict) and "range" in evidence:
            frozen = evidence["range"]
            if not isinstance(frozen, dict) or not {"base", "source_head"} <= frozen.keys():
                raise MDFError("Change evidence.range 需要 base 与 source_head", code="invalid_change")
            for key in ("base", "source_head", "target_head"):
                if key in frozen:
                    value = frozen[key]
                    if (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value) or sha(repo, value) != value
                            or (key != "target_head" and not ancestor(repo, value, head))):
                        raise MDFError("Change 固定范围不属于当前 source", code="invalid_change")
            if not ancestor(repo, frozen["base"], frozen["source_head"]):
                raise MDFError("Change 起点不属于原工作范围", code="invalid_change")
    if frozen is None:
        bases = git(repo, "merge-base", "--all", target_head, head, check=False).stdout.split()
        if len(bases) != 1:
            raise MDFError("Adhoc 需要唯一 merge-base；先明确工作范围", code="invalid_review_base")
        frozen = {"base": bases[0], "source_head": head}
    paths = git(repo, "diff", "--name-only", "-z", frozen["base"], head).stdout.split("\0")
    return {"source": source, "slug": root.name, "path": str(root.relative_to(repo)),
            "material_mode": "ledger" if ledger else "change", "head": head,
            "range": {**frozen, "target_head": target_head}, "target": "develop",
            "paths": [path for path in paths if path], "has_change": (root / "CHANGE.md").is_file()}


def complete_change(repo, source, root):
    from mdf_core.inspection.validate_change_schema import validate_change_file
    from mdf_core.lifecycle.roster import freeze_roster

    change = safe(repo, root / "CHANGE.md")
    if not change.is_file():
        raise MDFError("finish 前必须补齐 Change", code="missing_change")
    findings = []
    validate_change_file(repo, change, findings, expected_slug=root.name)
    if findings:
        raise MDFError("Adhoc Change 不完整", code="invalid_change",
                       details=[item.as_dict() for item in findings])
    metadata, _ = read_frontmatter(change)
    if metadata.get("source_branch") != source:
        raise MDFError("Change 与 source 不符", code="invalid_change")
    context(repo, source, root.name)
    return freeze_roster("adhoc")
