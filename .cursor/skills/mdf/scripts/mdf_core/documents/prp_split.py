"""先在临时副本校验完整拆分，再一次写入；写入故障恢复原文件。"""
import json
import re
import shutil
import tempfile
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import ensure_clean, repo_path, require_planning, require_git_root
from mdf_core.foundation.paths import ensure_safe_managed_paths, load_manifest
from mdf_core.documents.proposals import check_proposals, started
from mdf_core.foundation.constants import OBJECT_FILE_RE
from mdf_core.documents.html_documents import update_metadata, markdown_body


def render(meta, body):
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                                 for key, value in meta.items()) + "\n---\n\n" + body.strip() + "\n"


def split_plan(repo, spec):
    if not isinstance(spec, dict) or set(spec) != {"source", "children", "downstream", "rationale"}:
        raise MDFError("拆分输入需要 source/children/downstream/rationale", code="invalid_split")
    if not isinstance(spec["rationale"], str) or not spec["rationale"].strip():
        raise MDFError("需要范围覆盖与依赖分配的确认依据", code="invalid_split")
    objects = check_proposals(repo)
    source = spec["source"]
    if not isinstance(source, str) or source not in objects:
        raise MDFError("原 PRP 不存在", code="invalid_split")
    path, meta, body = objects[source]
    if (meta["status"] not in {"draft", "ready"} or len(path.relative_to(repo / "docs").parts) != 2
            or started(repo, source)):
        raise MDFError("仅未 start 的 active draft/ready 可以拆分", code="proposal_started")
    children = spec["children"]
    downstream = spec["downstream"]
    if not isinstance(children, list) or len(children) < 2 or not isinstance(downstream, dict):
        raise MDFError("拆分至少需要两个子 PRP 和下游映射", code="invalid_split")
    changed = {}
    ids = []
    for child in children:
        if not isinstance(child, dict) or set(child) != {"filename", "id", "depends_on", "body"}:
            raise MDFError("子项需要 filename/id/depends_on/body", code="invalid_split")
        name = child["filename"]
        match = OBJECT_FILE_RE.fullmatch(name) if isinstance(name, str) else None
        identifier = child["id"]
        if (not match or not name.endswith(".md") or not isinstance(identifier, str)
                or match.group(1) != identifier or not identifier.startswith("prp-")
                or identifier in objects or identifier in ids or not isinstance(child["body"], str)):
            raise MDFError("子 PRP 身份无效或冲突", code="invalid_split")
        target = repo / "docs/proposals" / name
        if target.exists():
            raise MDFError("子 PRP 路径已存在", code="collision")
        ids.append(identifier)
        child_meta = {"id": identifier, "type": "proposal", "status": "draft",
                      "depends_on": child["depends_on"]}
        if "milestone" in meta:
            child_meta["milestone"] = meta["milestone"]
        changed[target] = render(child_meta, child["body"])
    required = {key for key, value in objects.items() if source in value[1]["depends_on"]}
    if set(downstream) != required:
        raise MDFError("必须完整确认全部下游引用（包括历史对象）", code="invalid_split",
                       details={"required": sorted(required)})
    for identifier, replacements in downstream.items():
        if (not isinstance(replacements, list) or not replacements
                or any(not isinstance(item, str) or item not in ids for item in replacements)
                or len(set(replacements)) != len(replacements)):
            raise MDFError("下游替代依赖必须是非空且不重复的子 PRP ID", code="invalid_split")
        other_path, other_meta, other_body = objects[identifier]
        other_meta = dict(other_meta)
        other_meta["depends_on"] = list(dict.fromkeys(
            [dep for dep in other_meta["depends_on"] if dep != source] + replacements))
        changed[other_path] = (update_metadata(other_path.read_text(), other_meta)
                               if other_path.suffix == ".html" else render(other_meta, other_body))
    meta = {**meta, "status": "replaced", "replaced_by": ids}
    rationale = "\n\n## 拆分依据\n\n" + spec["rationale"]
    changed[path] = (re.sub(r"</main>", lambda _: markdown_body(rationale) + "\n</main>",
                          update_metadata(path.read_text(), meta), count=1, flags=re.IGNORECASE)
        if path.suffix == ".html"
        else render(meta, body + rationale))
    with tempfile.TemporaryDirectory(prefix="mdf-split-") as tmp:
        stage = Path(tmp).resolve()
        for directory in ("docs/proposals", "docs/bugs", "changes", "docs/context/adr"):
            src = repo / directory
            if src.exists():
                shutil.copytree(src, stage / directory, symlinks=True)
        for target, text in changed.items():
            dest = stage / target.relative_to(repo)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
        check_proposals(stage)
    return changed


def command_split(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    require_planning(repo)
    ensure_safe_managed_paths(repo)
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("当前操作需要 ready 仓库", code="manifest_not_ready")
    ensure_clean(repo)
    try:
        spec = json.loads(Path(args.spec_file).read_text())
    except ValueError as exc:
        raise MDFError("拆分输入必须是 JSON", code="invalid_split") from exc
    changed = split_plan(repo, spec)
    if not args.dry_run:
        before = {path: path.read_bytes() if path.exists() else None for path in changed}
        try:
            for path, content in changed.items():
                path.write_text(content)
        except OSError:
            for path, content in before.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)
            raise
    emit({"ok": True, "operation": "prp-split", "dry_run": args.dry_run,
          "files": {str(path.relative_to(repo)): content for path, content in changed.items()}})
