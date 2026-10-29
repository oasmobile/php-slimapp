"""独立 fact audit quick：只检查选中文档的 evidence 有效性与 Git stale。"""
import argparse
from pathlib import Path
from typing import Any

from mdf_core.execution.modules import load_modules
from mdf_core.foundation.errors import Finding, MDFError, add_finding, serialize_findings
from mdf_core.foundation.paths import relative
from mdf_core.foundation.progress import ProgressPlan, report_progress, skip_progress_group
from mdf_core.foundation.yamlutil import read_frontmatter
from mdf_core.inspection.audit import _changed_paths, _resolve_base, _scope_paths
from mdf_core.inspection.doc_size import size_role
from mdf_core.inspection.validate_evidence import fact_documents, frontmatter_evidence, validate_evidence
from mdf_core.workspace.gitutil import run


def _affected_documents(repo: Path, facts: set[Path], changed: list[Path]) -> set[Path]:
    """包含删除路径、目录 evidence 与 generated 依赖；无法解析的页面不能静默漏掉。"""
    documents = facts.intersection(changed)
    if not changed:
        return documents
    for document in facts:
        try:
            metadata, _ = read_frontmatter(document)
        except MDFError:
            documents.add(document)
            continue
        references = frontmatter_evidence(metadata)
        generated = metadata.get("generated")
        if isinstance(generated, dict):
            references += [value for key in ("source", "generator")
                           if isinstance(value := generated.get(key), str)]
        for raw in references:
            evidence = (repo / raw).resolve()
            if any(path == evidence or evidence in path.parents for path in changed):
                documents.add(document)
                break
    return documents


def quick_payload(repo: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    scope = args.scope or "full"
    findings: list[Finding] = []
    base = None
    sources: list[Path] = []
    documents: list[Path] = []
    ignored: list[str] = []
    plan = ProgressPlan("fact-audit quick", ("解析范围", "检查 evidence stale"), groups=("事实文档",))
    with plan.stage(1):
        if run(["git", "rev-parse", "--is-shallow-repository"], cwd=repo).stdout.strip() == "true":
            add_finding(findings, "audit.shallow", "quick 需要完整 Git history，无法在 shallow checkout 判断 stale")
        if scope == "full" and (args.base is not None or args.implementation_path or args.document_path):
            add_finding(findings, "audit.scope", "full audit accepts no explicit paths or base")
        elif scope == "branch" and (args.implementation_path or args.document_path):
            add_finding(findings, "audit.scope", "branch audit accepts no explicit paths")
        elif scope == "paths" and (args.base is not None or not (args.implementation_path or args.document_path)):
            add_finding(findings, "audit.scope", "paths audit requires paths and accepts no base")
        if not findings:
            modules = load_modules(repo)
            facts = set(fact_documents(repo))
            if scope == "full":
                documents = sorted(facts)
            elif scope == "branch":
                base = _resolve_base(repo, args.base, findings)
                changed = _changed_paths(repo, base) if base else []
                sources = [path for path in changed if modules.owns(relative(repo, path))
                           and size_role(relative(repo, path)) is None
                           and not modules.is_ignored(relative(repo, path))]
                documents = sorted(_affected_documents(repo, facts, sources) | facts.intersection(changed))
            else:
                sources, documents = _scope_paths(
                    repo, args.implementation_path, args.document_path, [], modules, facts, findings,
                )
                sources = [path for path in sources if modules.owns(relative(repo, path))
                           and not modules.is_ignored(relative(repo, path))]
                documents = sorted(set(documents) | _affected_documents(repo, facts, sources))
            ignored = [relative(repo, path) for path in documents if modules.is_ignored(relative(repo, path))]
            documents = [path for path in documents if relative(repo, path) not in ignored]
        report_progress("quick 范围", f"scope={scope}，文档 {len(documents)} 份；不审阅语义与覆盖")
    with plan.stage(2):
        if findings:
            skip_progress_group("事实文档", "范围或 Git history 无效")
        else:
            validate_evidence(repo, findings, check_staleness=True, documents=documents, freshness_only=True)
    payload = {
        "ok": not findings, "operation": "audit", "mode": "quick", "scope": scope,
        "semantic_review": False, "repo": str(repo), "base": base,
        "document_paths": [relative(repo, path) for path in documents],
        "ignored": ignored, "finding_count": len(findings), "findings": serialize_findings(findings),
    }
    return payload, 0 if not findings else 2
