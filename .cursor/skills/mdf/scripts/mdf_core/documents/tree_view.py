"""只读生成 draft/ready Proposal 混态依赖视图。"""
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import repo_path, require_git_root
from mdf_core.documents.proposals import check_proposals, started_ids
from mdf_core.inspection.validate_records import unsatisfied_depends_on


def _title(objects, key):
    return next((line[2:].strip() for line in objects[key][2].splitlines()
                 if line.startswith("# ")), key)


def _milestone(meta):
    name = meta.get("milestone")
    return name if isinstance(name, str) and name.strip() else None


def _group_sort(name):
    return (name is not None, name or "")


def _ordered_roots(shown, prp_waiting, waiting, objects, active):
    roots = [key for key in shown if not prp_waiting[key]]
    buckets = {}
    for key in roots:
        buckets.setdefault(_milestone(objects[key][1]), []).append(key)
    names = set(buckets)
    incoming = {name: set() for name in names}
    outgoing = {name: set() for name in names}
    for key in roots:
        src = _milestone(objects[key][1])
        for dep in waiting[key]:
            if dep in active or dep not in names or dep == src:
                continue
            incoming[src].add(dep)
            outgoing[dep].add(src)
    ready = sorted((name for name, preds in incoming.items() if not preds),
                   key=_group_sort)
    ordered = []
    while ready:
        name = ready.pop(0)
        ordered.append(name)
        nxts = []
        for nxt in outgoing[name]:
            incoming[nxt].discard(name)
            if not incoming[nxt] and nxt not in ordered and nxt not in ready:
                nxts.append(nxt)
        ready.extend(nxts)
        ready.sort(key=_group_sort)
    for name in sorted(names, key=_group_sort):
        if name not in ordered:
            ordered.append(name)
    return [key for name in ordered for key in sorted(buckets[name])]


def _index(objects, waiting, in_progress, active_ids):
    groups, ungrouped = {}, []
    for key in active_ids:
        meta = objects[key][1]
        item = {"id": key, "title": _title(objects, key),
                "status": meta["status"],
                "depends_on": list(meta["depends_on"]),
                "blocked_by": waiting[key],
                "in_progress": key in in_progress}
        milestone = _milestone(meta)
        if milestone is not None:
            groups.setdefault(milestone, []).append(item)
        else:
            ungrouped.append(item)
    return {"groups": [{"milestone": name, "items": groups[name]}
                       for name in sorted(groups)],
            "ungrouped": ungrouped}


_LEGEND = (
    "● ready  ○ draft  * in_progress  ↩ 交叉引用  "
    "[milestone]  ↑ 上一组 milestone"
)


def _is_prp(name):
    return isinstance(name, str) and name.startswith("prp-")


def _label(node, omit_ms):
    if node.get("reference"):
        blocked = ", ".join(node.get("blocked_by") or [])
        suffix = f" ← {blocked}" if blocked else ""
        return f"↩ {node['id']}{suffix}"
    star = "*" if node.get("in_progress") else ""
    extra = ""
    milestone = node.get("milestone")
    if milestone and not omit_ms:
        extra = f" [{milestone}]"
    mark = "●" if node["status"] == "ready" else "○"
    return f"{mark} {node['id']} {node['title']}{star}{extra}"


def _child_lines(children, prefix, group_ms):
    lines = []
    total = len(children)
    for index, child in enumerate(children):
        last = index == total - 1
        branch = "└ " if last else "├ "
        extend = "  " if last else "│ "
        same = group_ms is not None and child.get("milestone") == group_ms
        lines.append(prefix + branch + _label(child, same))
        if not child.get("reference"):
            lines.extend(_child_lines(
                child.get("children") or [], prefix + extend, group_ms
            ))
    return lines


def _root_groups(trees):
    groups = []
    for node in trees:
        name = node.get("milestone")
        if groups and groups[-1][0] == name:
            groups[-1][1].append(node)
        else:
            groups.append((name, [node]))
    return groups


def _md_cell(value):
    if value is True:
        text = "true"
    elif value is False:
        text = "false"
    elif isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    elif value is None:
        text = ""
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _table_row(values):
    return "| " + " | ".join(_md_cell(value) for value in values) + " |"


_TABLE_COLUMNS = (
    "id", "title", "status", "in_progress", "depends_on", "blocked_by",
    "milestone",
)


def render_table(index, hidden):
    lines = [
        _table_row(_TABLE_COLUMNS),
        "| " + " | ".join("---" for _ in _TABLE_COLUMNS) + " |",
    ]
    for item in index["ungrouped"]:
        lines.append(_table_row([
            item["id"], item["title"], item["status"], item["in_progress"],
            item["depends_on"], item["blocked_by"], "",
        ]))
    for group in index["groups"]:
        for item in group["items"]:
            lines.append(_table_row([
                item["id"], item["title"], item["status"],
                item["in_progress"], item["depends_on"], item["blocked_by"],
                group["milestone"],
            ]))
    hidden_line = "hidden: " + ", ".join(hidden) if hidden else "hidden:"
    return "\n".join(lines + ["", hidden_line])


def render_diagram(trees, empty):
    if empty:
        return "无 draft 且无 ready。"
    lines = [_LEGEND, ""]
    previous = None
    for name, roots in _root_groups(trees):
        if previous is not None and any(
            previous in (node.get("blocked_by") or []) for node in roots
        ):
            lines.append("↑")
        if name is not None:
            lines.append(f"[{name}]")
        omit = name is not None
        for node in roots:
            for dep in node.get("blocked_by") or []:
                if not _is_prp(dep) and dep != previous:
                    lines.append(f"↑ {dep}")
            lines.append(_label(node, omit))
            lines.extend(_child_lines(node.get("children") or [], "", name))
        previous = name
    return "\n".join(lines)


def tree_view(repo, depth):
    if type(depth) is not int or depth < 1:
        raise MDFError("depth 必须为正整数", code="invalid_depth")
    objects = check_proposals(repo)
    active = {key: value for key, value in objects.items()
              if value[1]["status"] in {"draft", "ready"}}
    metas = {key: value[1] for key, value in objects.items()}
    waiting = {key: unsatisfied_depends_on(value[1]["depends_on"], metas)
               for key, value in active.items()}
    prp_waiting = {key: [dep for dep in waiting[key] if dep in active]
                   for key in active}
    in_progress = started_ids(repo)
    levels = {}

    def level(key):
        if key in levels:
            return levels[key]
        parents = [level(dep) for dep in prp_waiting[key]]
        levels[key] = None if None in parents else 1 + max(parents, default=0)
        return levels[key]

    for key in sorted(active):
        level(key)
    shown = {key for key, value in levels.items()
             if value is not None and value <= depth}
    seen = set()

    def node(key):
        meta = objects[key][1]
        result = {"id": key, "level": levels[key], "status": meta["status"],
                  "blocked_by": waiting[key],
                  "in_progress": key in in_progress,
                  "title": _title(objects, key)}
        milestone = _milestone(meta)
        if milestone is not None:
            result["milestone"] = milestone
        if key in seen:
            result["reference"] = True
            return result
        seen.add(key)
        result["children"] = [node(child) for child in sorted(shown)
                              if key in prp_waiting[child]]
        return result

    trees = [node(key) for key in _ordered_roots(
        shown, prp_waiting, waiting, objects, active)]
    empty = not active
    index = _index(objects, waiting, in_progress, sorted(active))
    hidden = sorted(key for key, value in levels.items()
                    if value is not None and value > depth)
    return {"ok": True, "operation": "tree", "depth": depth, "trees": trees,
            "index": index, "hidden": hidden, "empty": empty,
            "diagram": render_diagram(trees, empty),
            "table": render_table(index, hidden)}


def command_tree(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    from mdf_core.foundation.paths import load_manifest, ensure_safe_managed_paths
    ensure_safe_managed_paths(repo)
    if load_manifest(repo).get("state") != "ready":
        raise MDFError("当前操作需要 ready 仓库", code="manifest_not_ready")
    emit(tree_view(repo, args.depth))
