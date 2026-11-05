import os
from functools import partial
from pathlib import Path
from typing import Any, Iterable

from mdf_core.foundation.constants import (
    DOC_TYPES,
    FACT_ROOTS,
    MARKER_RE,
    MDF_BLOCK_END,
    MDF_BLOCK_START,
    SYSTEM_DOC_TYPES,
    USER_GUIDE_DOC_TYPE,
)
from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.workspace.gitutil import GitPathIndex
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.foundation.progress import (
    progress, progress_items, register_progress_groups, report_progress, skip_progress_group,
)
from mdf_core.foundation.yamlutil import read_frontmatter
from mdf_core.inspection.parallel import collect_parallel


def frontmatter_evidence(metadata: dict[str, Any]) -> list[str]:
    """evidence 仅为 path 列表（允许字符串或 {path: ...}，忽略其余键）。"""
    raw = metadata.get("evidence")
    result: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                path = item["path"].strip()
                if path:
                    result.append(path)
    elif isinstance(raw, dict):
        paths = raw.get("paths")
        if isinstance(paths, list):
            for path in paths:
                if isinstance(path, str) and path.strip():
                    result.append(path.strip())
    return result


def fact_documents(repo: Path) -> Iterable[Path]:
    found: set[Path] = set()
    for raw in FACT_ROOTS:
        root = repo / raw
        if root.is_symlink() or not path_stays_in_repo(repo, root):
            continue
        if root.is_dir():
            found.update(
                path
                for path in root.rglob("*.md")
                if path.is_file()
                and not path.is_symlink()
                and path_stays_in_repo(repo, path)
            )
        elif root.is_file():
            found.add(root)
    return sorted(found)


RECORD_FILES = (".mdf/manifest.yaml", "CHANGELOG.md", "docs/JOTS.md")
RECORD_DIRS = ("changes/", "docs/proposals/", "docs/bugs/")


def _is_record(rel: str) -> bool:
    return rel in RECORD_FILES or rel.startswith(RECORD_DIRS)


def validate_evidence(
    repo: Path,
    findings: list[Finding],
    *,
    check_staleness: bool,
    documents: list[Path] | None = None,
    freshness_only: bool = False,
) -> None:
    with progress("事实文档：扫描文档"):
        all_documents = list(fact_documents(repo))
        fact_paths = {doc.resolve() for doc in all_documents}
        if documents is None:
            documents = all_documents
    # 小范围继续按需查询；较多页面共享一次有限 history 预取。
    index = GitPathIndex(repo, batch_history=check_staleness and len(documents) >= 8)
    register_progress_groups(
        [f"evidence：{relative(repo, doc)}" for doc in documents], reason="文档扫描完成",
    )
    report_progress(
        "事实文档计数计划",
        f"局部计数组共 {1 + len(documents)} 组：文档汇总 1 组，共 {len(documents)} 页；"
        f"逐页 evidence {len(documents)} 组，并行执行；各组总量读取对应页面后确定",
    )

    def inspect(doc: Path) -> list[Finding]:
        findings: list[Finding] = []
        rel = relative(repo, doc)
        try:
            metadata, body = read_frontmatter(doc)
        except MDFError as exc:
            add_finding(findings, "fact.frontmatter", str(exc), rel)
            skip_progress_group(f"evidence：{rel}", "页面无法解析，总量无法确定")
            return findings
        if not freshness_only:
            if metadata.get("doc_type") not in DOC_TYPES:
                add_finding(
                    findings,
                    "fact.doc_type",
                    "Fact document requires a supported doc_type",
                    rel,
                )
            else:
                parts = Path(rel).parts
                expected_doc_type: str | None = None
                if len(parts) >= 3 and parts[:2] == ("docs", "user-guide"):
                    expected_doc_type = USER_GUIDE_DOC_TYPE
                elif len(parts) >= 3 and parts[:2] == ("docs", "system"):
                    selector = parts[2]
                    expected_doc_type = SYSTEM_DOC_TYPES.get(selector)
                if expected_doc_type is None:
                    add_finding(
                        findings,
                        "fact.path",
                        "Fact document is outside a supported user-guide/system "
                        "view",
                        rel,
                    )
                elif metadata.get("doc_type") != expected_doc_type:
                    add_finding(
                        findings,
                        "fact.doc_type_path",
                        f"doc_type must be {expected_doc_type} at this path",
                        rel,
                    )
            if MARKER_RE.search(body):
                add_finding(
                    findings,
                    "fact.marker",
                    "Fact document contains an unresolved template marker",
                    rel,
                )
        evidence = frontmatter_evidence(metadata)
        generated = metadata.get("generated")
        if not evidence:
            add_finding(
                findings,
                "evidence.missing",
                "Current-fact document needs at least one evidence path",
                rel,
            )
        doc_tracked = index.tracked(doc) if check_staleness else True
        if check_staleness and not doc_tracked:
            add_finding(
                findings,
                "fact.untracked",
                "Current-fact document is not tracked by Git",
                rel,
            )
        doc_commit = index.last_commit(doc) if check_staleness else None
        for evidence_path in progress_items(f"evidence：{rel}", evidence):
            raw_candidate = Path(evidence_path)
            candidate = (repo / raw_candidate).resolve()
            if raw_candidate.is_absolute():
                add_finding(
                    findings,
                    "evidence.outside_repo",
                    f"Evidence must be repository-relative: {evidence_path}",
                    rel,
                )
                continue
            try:
                candidate.relative_to(repo)
            except ValueError:
                add_finding(
                    findings,
                    "evidence.outside_repo",
                    f"Evidence is outside the repository: {evidence_path}",
                    rel,
                )
                continue
            if not candidate.exists():
                add_finding(
                    findings,
                    "evidence.missing_path",
                    f"Evidence path does not exist: {evidence_path}",
                    rel,
                )
                continue
            if _is_record(relative(repo, candidate)):
                add_finding(
                    findings,
                    "evidence.record",
                    "发版流程会改写的记录文件不能作为 evidence，改引实现、测试或配置: "
                    f"{evidence_path}",
                    rel,
                )
                continue
            # 事实页之间的引用只是链接；不比较先后。
            if not check_staleness or candidate in fact_paths:
                continue
            if not index.tracked(candidate):
                add_finding(
                    findings,
                    "evidence.untracked",
                    f"Evidence is not tracked by Git: {evidence_path}",
                    rel,
                )
                continue
            evidence_commit = index.last_commit(candidate)
            if index.dirty(candidate) or doc_commit is None or (freshness_only and evidence_commit is None):
                add_finding(
                    findings,
                    "evidence.stale",
                    f"Evidence requires revalidation: {evidence_path}",
                    rel,
                )
            elif evidence_commit is not None and index.commit_is_after(
                evidence_commit, doc_commit
            ):
                add_finding(
                    findings,
                    "evidence.stale",
                    f"Evidence changed after this document: {evidence_path}",
                    rel,
                )
        if isinstance(generated, dict):
            source = generated.get("source")
            generator = generated.get("generator")
            source_path: Path | None = None
            generator_path: Path | None = None
            report_progress(f"generated：{rel}", f"检查 source：{source}")
            if not isinstance(source, str) or not source.strip():
                add_finding(
                    findings,
                    "generated.source",
                    "Generated documents require generated.source",
                    rel,
                )
            else:
                raw_source = Path(source)
                source_path = (repo / raw_source).resolve()
                if raw_source.is_absolute() or not path_stays_in_repo(
                    repo, source_path
                ):
                    add_finding(
                        findings,
                        "generated.outside_repo",
                        "Generated source must be repository-relative: "
                        f"{source}",
                        rel,
                    )
                    source_path = None
                elif not source_path.exists():
                    add_finding(
                        findings,
                        "generated.source_missing",
                        f"Generated source does not exist: {source}",
                        rel,
                    )
                    source_path = None
                elif check_staleness and not index.tracked(source_path):
                    add_finding(
                        findings,
                        "generated.untracked",
                        f"Generated source is not tracked by Git: {source}",
                        rel,
                    )
            report_progress(f"generated：{rel}", f"检查 generator：{generator}")
            if not isinstance(generator, str) or not generator.strip():
                add_finding(
                    findings,
                    "generated.generator",
                    "Generated documents require generated.generator",
                    rel,
                )
            else:
                raw_generator = Path(generator)
                generator_path = (repo / raw_generator).resolve()
                if raw_generator.is_absolute() or not path_stays_in_repo(
                    repo, generator_path
                ):
                    add_finding(
                        findings,
                        "generated.outside_repo",
                        f"Generator must be repository-relative: {generator}",
                        rel,
                    )
                    generator_path = None
                elif not generator_path.is_file():
                    add_finding(
                        findings,
                        "generated.generator_missing",
                        f"Generator does not exist: {generator}",
                        rel,
                    )
                    generator_path = None
                elif not os.access(generator_path, os.X_OK):
                    add_finding(
                        findings,
                        "generated.generator_not_executable",
                        f"Generator is not executable: {generator}",
                        rel,
                    )
                    generator_path = None
                elif check_staleness and not index.tracked(generator_path):
                    add_finding(
                        findings,
                        "generated.untracked",
                        f"Generator is not tracked by Git: {generator}",
                        rel,
                    )
                    generator_path = None
            if check_staleness:
                for label, generated_path in (
                    ("source", source_path),
                    ("generator", generator_path),
                ):
                    if generated_path is None:
                        continue
                    report_progress(
                        f"generated：{rel}",
                        f"检查 {label} Git history：{relative(repo, generated_path)}",
                    )
                    generated_commit = index.last_commit(generated_path)
                    if (
                        index.dirty(generated_path)
                        or doc_commit is None
                        or generated_commit is None
                        or index.commit_is_after(generated_commit, doc_commit)
                    ):
                        add_finding(
                            findings,
                            "generated.stale",
                            f"Generated {label} requires revalidation",
                            rel,
                        )

        return findings

    findings.extend(collect_parallel([
        (f"事实文档：{relative(repo, doc)}", partial(inspect, doc)) for doc in documents
    ], label="事实文档"))


def validate_agents_block(repo: Path, findings: list[Finding]) -> None:
    path = repo / "AGENTS.md"
    if not path.is_file():
        add_finding(
            findings, "agents.missing", "Missing AGENTS.md", "AGENTS.md"
        )
        return
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        add_finding(
            findings,
            "path.symlink",
            "AGENTS.md must be a regular repository file",
            "AGENTS.md",
        )
        return
    text = path.read_text(encoding="utf-8")
    starts = text.count(MDF_BLOCK_START)
    ends = text.count(MDF_BLOCK_END)
    if (
        starts != 1
        or ends != 1
        or text.index(MDF_BLOCK_START) > text.index(MDF_BLOCK_END)
    ):
        add_finding(
            findings,
            "agents.block",
            "AGENTS.md must contain exactly one valid MDF managed block",
            "AGENTS.md",
        )
