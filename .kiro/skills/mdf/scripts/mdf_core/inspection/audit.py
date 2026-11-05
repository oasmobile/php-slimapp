import argparse
from functools import partial
from pathlib import Path
from typing import Any

from mdf_core.inspection import doctor
from mdf_core.inspection.code_size import is_source
from mdf_core.inspection.doc_size import sizable_documents, size_findings, size_role, structure_findings
from mdf_core.foundation.errors import Finding, MDFError, add_finding, emit, has_errors, serialize_findings
from mdf_core.workspace.gitutil import git_path_tracked, repo_path, require_git_root, run
from mdf_core.inspection.overview_modules import overview_core_module_findings, project_entry_link_findings
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.foundation.progress import ProgressPlan, report_progress
from mdf_core.execution.modules import MODULES_PATH, ModulesConfig, load_modules, match
from mdf_core.inspection.validate_evidence import fact_documents, frontmatter_evidence
from mdf_core.inspection.validate_manifest import implementation_roots
from mdf_core.inspection.parallel import collect_parallel
from mdf_core.foundation.yamlutil import read_frontmatter

# 不承载行为的被跟踪实现文件：版本钉、锁文件与本地配置。
# 它们不产生 audit.uncovered warning，也无需写入 evidence 或 ignorelist。
NON_BEHAVIORAL_NAMES = {
    ".gitattributes",
    ".gitignore",
    ".node-version",
    ".nvmrc",
    ".python-version",
    ".tool-versions",
    "Cargo.lock",
    "Gemfile.lock",
    "Pipfile.lock",
    "composer.lock",
    "go.sum",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "rust-toolchain.toml",
    "uv.lock",
    "yarn.lock",
}


def _tracked_files(repo: Path, roots: list[Path]) -> list[Path]:
    result = run(["git", "ls-files", "-z"], cwd=repo)
    paths = []
    for raw in result.stdout.split("\0"):
        if not raw:
            continue
        path = (repo / raw).resolve()
        if (
            path.is_file()
            and not path.is_symlink()
            and any(path == root or root in path.parents for root in roots)
        ):
            paths.append(path)
    return sorted(set(paths))


def _scope_paths(
    repo: Path,
    implementation_paths: list[str],
    document_paths: list[str],
    roots: list[Path],
    modules: ModulesConfig,
    facts: set[Path],
    findings: list[Finding],
) -> tuple[list[Path], list[Path]]:
    implementation: list[Path] = []
    documents: list[Path] = []
    for raw in implementation_paths:
        candidate = Path(raw)
        path = (repo / candidate).resolve()
        if candidate.is_absolute() or not path_stays_in_repo(repo, path):
            add_finding(
                findings,
                "audit.scope_path",
                "scope path is outside repository",
                raw,
            )
            continue
        if (
            path.is_file()
            and not path.is_symlink()
            and git_path_tracked(repo, path)
            and (any(root in path.parents for root in roots) or is_source(path) or modules.owns(relative(repo, path)))
        ):
            implementation.append(path)
        else:
            add_finding(
                findings, "audit.scope_path", "scope path is invalid", raw
            )
    for raw in document_paths:
        candidate = Path(raw)
        path = (repo / candidate).resolve()
        if candidate.is_absolute() or not path_stays_in_repo(repo, path):
            add_finding(
                findings,
                "audit.scope_path",
                "scope path is outside repository",
                raw,
            )
        elif path in facts:
            documents.append(path)
        else:
            add_finding(
                findings, "audit.scope_path", "scope path is invalid", raw
            )
    return sorted(set(implementation)), sorted(set(documents))


def _resolve_base(repo: Path, base: str | None, findings: list[Finding]) -> str | None:
    if base is None:
        result = run(["git", "merge-base", "develop", "HEAD"], cwd=repo, check=False)
        if result.returncode:
            add_finding(
                findings, "audit.base",
                "branch audit needs --base or a local develop branch",
            )
            return None
        return result.stdout.strip()
    result = run(
        ["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
        cwd=repo, check=False,
    )
    if result.returncode:
        add_finding(findings, "audit.base", "branch audit base is not a commit", base)
        return None
    return result.stdout.strip()


def _changed_paths(repo: Path, base: str) -> list[Path]:
    """base 到当前工作区（含未提交）的改动路径；rename 保留新旧两端。"""
    result = run(
        ["git", "diff", "--name-only", "--no-renames", "--ignore-submodules=none", "-z", base, "--"], cwd=repo,
    )
    return sorted(
        {
            (repo / raw).resolve()
            for raw in result.stdout.split("\0")
            if raw and path_stays_in_repo(repo, (repo / raw).resolve())
        }
    )


def _branch_scope(
    repo: Path,
    all_sources: list[Path],
    facts: set[Path],
    changed: list[Path],
) -> tuple[list[Path], list[Path]]:
    """实现范围是改动到的实现文件；文档范围是改动到的事实页及 evidence 引用这些实现的事实页。"""
    source_set = set(all_sources)
    implementation = [path for path in changed if path in source_set]
    documents = {path for path in changed if path in facts}
    touched = set(implementation)
    for document in facts:
        try:
            metadata, _ = read_frontmatter(document)
        except MDFError:
            continue
        for raw in frontmatter_evidence(metadata):
            if (repo / raw).resolve() in touched:
                documents.add(document)
                break
    return implementation, sorted(documents)


def _ignored_paths(
    repo: Path, sources: list[Path], findings: list[Finding], config: ModulesConfig,
    *, validation_paths: list[str] | None = None,
) -> tuple[dict[Path, dict[str, str]], set[str]]:
    """返回命中记录与完整 pattern 集，删除路径仍按全部规则判定范围。"""
    result: dict[Path, dict[str, str]] = {}
    for owner, rule in config.all_ignore_rules():
        matched = [item for item in sources
                   if config.ignore_matches(relative(repo, item), owner, rule)]
        valid = bool(matched) if validation_paths is None else any(
            config.ignore_matches(path, owner, rule) for path in validation_paths
        )
        if not valid:
            add_finding(findings, "audit.ignore_empty",
                        "ignore pattern matches no tracked file in its scope",
                        f"{owner or 'repo'}:{rule.pattern}")
            continue
        for item in matched:
            if config.is_ignored(relative(repo, item)):
                result.setdefault(item, {"path": rule.pattern, "reason": rule.reason, "module": owner})
    return result, {rule.pattern for _, rule in config.all_ignore_rules()}


def audit_payload(
    repo: Path,
    scope: str,
    implementation_paths: list[str],
    document_paths: list[str],
    base: str | None = None,
    *,
    extra_documents: list[str] = (),
    ignore_modules: ModulesConfig | None = None,
    ignore_paths: list[str] | None = None,
    scope_changes: list[str] | None = None,
) -> tuple[dict[str, Any], int]:
    plan = ProgressPlan("fact-audit", ("全量契约校验", "解析范围", "检查文档结构", "映射 evidence 与覆盖"),
                        groups=("契约检查", "事实文档", "文档结构检查"))
    with plan.stage(1):
        findings = doctor.collect_findings(repo, full=True)
    with plan.stage(2):
        from mdf_core.foundation.paths import load_manifest
        roots = implementation_roots(repo, load_manifest(repo), [])
        facts = set(fact_documents(repo))
        all_tracked = _tracked_files(repo, [repo])
        try:
            size_config = ignore_modules if ignore_modules is not None else load_modules(repo)
        except MDFError as exc:
            add_finding(findings, "modules.invalid", str(exc), MODULES_PATH)
            size_config = ModulesConfig()
        ignored, ignored_patterns = _ignored_paths(repo, all_tracked, findings, size_config,
                                                  validation_paths=ignore_paths)
        all_sources = [path for path in all_tracked if size_config.owns(relative(repo, path))
                       and size_role(relative(repo, path)) is None]
        resolved_base: str | None = None
        sized: list[Path]
        if scope == "full":
            if implementation_paths or document_paths or base is not None:
                add_finding(
                    findings, "audit.scope", "full audit accepts no explicit paths"
                )
            sources, documents = all_sources, sorted(facts)
            sized = sizable_documents(repo)
            code_paths = all_tracked
        elif scope == "branch":
            if implementation_paths or document_paths:
                add_finding(
                    findings, "audit.scope", "branch audit accepts no explicit paths"
                )
            resolved_base = _resolve_base(repo, base, findings)
            changed = _changed_paths(repo, resolved_base) if resolved_base else []
            if scope_changes is not None:
                changed = [repo / p for p in scope_changes]
            changed = [p for p in changed if (size_config.owns(relative(repo, p))
                       or p in facts or size_role(relative(repo, p)) is not None)]
            code_paths = [path for path in changed if git_path_tracked(repo, path)]
            sources, documents = _branch_scope(repo, all_sources, facts,
                                               [p for p in changed if p not in ignored])
            documents = sorted(set(documents) | {repo / p for p in extra_documents if repo / p in facts})
            sized = documents + [
                path for path in changed
                if path not in facts and size_role(relative(repo, path)) is not None
            ]
        else:
            if not implementation_paths and not document_paths:
                add_finding(
                    findings, "audit.scope", "paths audit requires explicit paths"
                )
            if base is not None:
                add_finding(findings, "audit.scope", "--base only applies to branch scope")
            sources, documents = _scope_paths(
                repo,
                implementation_paths,
                document_paths,
                roots,
                size_config,
                facts,
                findings,
            )
            sized = documents
            code_paths = sources
        # 实现按 module 归属过滤；事实页独立检查自身的 ignore。
        checked_paths = set(sources + code_paths + sized)
        sources = [path for path in sources if path not in ignored and size_config.owns(relative(repo, path))]
        documents = [path for path in documents if path not in ignored]
        sized = [path for path in sized if path not in ignored]
        report_progress(
            "fact-audit 范围",
            f"scope={scope}，实现 {len(sources)} 份，文档 {len(documents)} 份",
        )
    with plan.stage(3):
        findings.extend(collect_parallel([
            ("文档体积", partial(size_findings, repo, sized)),
            ("文档结构", partial(structure_findings, repo, sized)),
            ("核心模块表", partial(overview_core_module_findings, repo, documents)),
            ("项目入口", partial(project_entry_link_findings, repo, sized)),
        ], label="文档结构检查"))
    with plan.stage(4):
        mappings: list[dict[str, Any]] = []
        covered: set[Path] = set()
        source_set = set(sources)
        for document in documents:
            try:
                metadata, _ = read_frontmatter(document)
            except MDFError:
                evidence: list[str] = []
            else:
                evidence = frontmatter_evidence(metadata)
            resolved = []
            for raw in evidence:
                candidate = (repo / raw).resolve()
                if candidate in source_set:
                    covered.add(candidate)
                resolved.append(raw)
            mappings.append(
                {"document": relative(repo, document), "evidence": resolved}
            )
        warnings = [
            Finding(
                "audit.uncovered", "implementation file has no fact evidence",
                relative(repo, path), "warning",
            )
            for path in sources
            if path not in covered
            and path not in ignored
            and path.name not in NON_BEHAVIORAL_NAMES
        ]
    payload = {
        "ok": not has_errors(findings),
        "operation": "audit",
        "scope": scope,
        "base": resolved_base,
        "repo": str(repo),
        "implementation_paths": [relative(repo, path) for path in sources],
        "document_paths": [relative(repo, path) for path in documents],
        "mappings": mappings,
        "ignored": [
            {
                "path": relative(repo, path),
                "ignore_path": rule["path"],
                "reason": rule["reason"],
            }
            for path, rule in sorted(ignored.items())
            if path in checked_paths or relative(repo, path) == "AGENTS.md"
        ],
        "warning_count": len(warnings),
        "warnings": serialize_findings(warnings),
        "finding_count": len(findings),
        "findings": serialize_findings(findings),
    }
    return payload, 0 if not has_errors(findings) else 2


def command_audit(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    if args.quick:
        if args.against is not None:
            raise MDFError('quick 不能与 against 混用', code='invalid_arguments')
        from mdf_core.inspection.audit_quick import quick_payload
        payload, exit_code = quick_payload(repo, args)
        emit(payload)
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args.against is not None:
        if not args.against or args.scope is not None or args.base is not None or args.implementation_path or args.document_path:
            raise MDFError('against 不能混用 scope/base/paths', code='invalid_arguments')
        from mdf_core.reviewing.fact_context import fact_context
        emit({'ok': True, 'result': fact_context(repo, args.against)})
        return
    payload, exit_code = audit_payload(
        repo,
        args.scope or "full",
        list(args.implementation_path),
        list(args.document_path),
        args.base,
    )
    emit(payload)
    if exit_code:
        raise SystemExit(exit_code)
