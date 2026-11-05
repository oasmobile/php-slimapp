"""只读列出 active Proposal 与 Bug，供 intent 定位对象而不逐篇翻阅。"""
from mdf_core.foundation.constants import BUG_SEVERITIES, BUG_STATUSES, OBJECT_FILE_RE
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import repo_path, require_git_root
from mdf_core.foundation.paths import ensure_safe_managed_paths, load_manifest, relative
from mdf_core.documents.proposals import started_ids
from mdf_core.inspection.validate_objects import iter_object_files
from mdf_core.inspection.validate_records import unsatisfied_depends_on
from mdf_core.foundation.yamlutil import read_frontmatter

PROPOSAL_STATUSES = {"draft", "ready", "implemented", "released", "rejected", "replaced"}
BUG_FIELDS = ("severity", "found_in", "fixed_in", "reject-reason", "duplicate_of")


def resolve_filters(kind, statuses, milestone, severity):
    if milestone is not None and severity is not None:
        raise MDFError("--milestone 与 --severity 不能同时使用", code="invalid_filter")
    implied = "proposal" if milestone is not None else "bug" if severity is not None else None
    if implied and kind and kind != implied:
        raise MDFError(f"--{'milestone' if implied == 'proposal' else 'severity'} 只适用于 {implied}",
                       code="invalid_filter")
    kind = kind or implied
    if severity is not None and severity not in BUG_SEVERITIES:
        raise MDFError("severity 必须是 critical、major 或 trivial", code="invalid_filter")
    allowed = PROPOSAL_STATUSES if kind == "proposal" else BUG_STATUSES if kind == "bug" \
        else PROPOSAL_STATUSES | BUG_STATUSES
    unknown = sorted(set(statuses) - allowed)
    if unknown:
        raise MDFError(f"未知状态: {', '.join(unknown)}", code="invalid_filter")
    return {"type": kind, "status": sorted(set(statuses)), "milestone": milestone, "severity": severity}


def title_of(body, fallback):
    return next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), fallback)


def scan(repo, kind, skipped):
    """返回 (active 条目列表, 全部可解析 Proposal 元数据)。"""
    entries, metas = [], {}
    for path in iter_object_files(repo, kind):
        rel = relative(repo, path)
        active = len(path.relative_to(repo / "docs").parts) == 2
        if not OBJECT_FILE_RE.fullmatch(path.name):
            if active:
                skipped.append({"path": rel, "reason": "文件名不符合对象命名"})
            continue
        try:
            meta, body = read_frontmatter(path)
        except (MDFError, OSError, UnicodeError) as exc:
            if active:
                skipped.append({"path": rel, "reason": str(exc)})
            continue
        identifier, status = meta.get("id"), meta.get("status")
        if not isinstance(identifier, str) or not isinstance(status, str):
            if active:
                skipped.append({"path": rel, "reason": "缺少字符串 id 或 status"})
            continue
        if kind == "proposal":
            metas[identifier] = meta
        if active:
            entries.append((path, rel, meta, body))
    return entries, metas


def proposal_entry(rel, meta, body, metas, in_progress):
    depends_on = meta.get("depends_on") if isinstance(meta.get("depends_on"), list) else []
    return {"id": meta["id"], "type": "proposal", "status": meta["status"], "title": title_of(body, meta["id"]),
            "path": rel, "depends_on": depends_on, "blocked_by": unsatisfied_depends_on(depends_on, metas),
            "in_progress": meta["id"] in in_progress, "milestone": meta.get("milestone")}


def bug_entry(rel, meta, body):
    result = {"id": meta["id"], "type": "bug", "status": meta["status"], "title": title_of(body, meta["id"]),
              "path": rel}
    result.update({key: meta.get(key) for key in BUG_FIELDS})
    return result


def matches(entry, filters):
    if filters["status"] and entry["status"] not in filters["status"]:
        return False
    if filters["milestone"] is not None and entry.get("milestone") != filters["milestone"]:
        return False
    return filters["severity"] is None or entry.get("severity") == filters["severity"]


def list_objects(repo, kind=None, statuses=(), milestone=None, severity=None):
    filters = resolve_filters(kind, list(statuses), milestone, severity)
    skipped, objects = [], []
    kinds = (filters["type"],) if filters["type"] else ("proposal", "bug")
    for current in kinds:
        entries, metas = scan(repo, current, skipped)
        if current == "proposal":
            in_progress = started_ids(repo) if entries else set()
            objects.extend(proposal_entry(rel, meta, body, metas, in_progress) for _, rel, meta, body in entries)
        else:
            objects.extend(bug_entry(rel, meta, body) for _, rel, meta, body in entries)
    objects = sorted((item for item in objects if matches(item, filters)), key=lambda item: item["id"])
    return {"ok": True, "operation": "list", "filters": filters, "count": len(objects),
            "objects": objects, "skipped": sorted(skipped, key=lambda item: item["path"])}


def command_list(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_safe_managed_paths(repo)
    load_manifest(repo)
    emit(list_objects(repo, args.type, args.status, args.milestone, args.severity))
