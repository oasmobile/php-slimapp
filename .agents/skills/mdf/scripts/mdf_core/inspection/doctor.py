from pathlib import Path

from mdf_core.foundation.errors import Finding, add_finding
from mdf_core.foundation.paths import is_local_artifact_root, managed_symlinks
from mdf_core.foundation.progress import (
    progress, register_progress_groups, report_count, report_progress, skip_progress_group,
)
from mdf_core.inspection.parallel import collect_parallel
from mdf_core.inspection.validate_changes import validate_changes
from mdf_core.inspection.validate_evidence import validate_agents_block, validate_evidence
from mdf_core.inspection.validate_jots import validate_jots
from mdf_core.inspection.validate_layout import validate_layout
from mdf_core.inspection.validate_links import validate_links
from mdf_core.inspection.validate_manifest import validate_manifest
from mdf_core.execution.modules_check import validate_modules
from mdf_core.inspection.validate_objects import iter_object_files, validate_object
from mdf_core.inspection.validate_records import validate_adrs, validate_record_references
from mdf_core.inspection.validate_release import validate_changelog, validate_release_history


def collect_uninitialized_findings(repo: Path) -> list[Finding]:
    """无 manifest 时仍检查布局，使退休目录能在分流前被看见。"""
    findings: list[Finding] = []
    register_progress_groups([], reason="未初始化，仅检查布局")
    skip_progress_group("事实文档", "未初始化，无事实文档检查")
    report_progress("契约检查计划", "共 1 个检查组：未初始化布局")
    report_count("契约检查", 0, 1)
    with progress("契约：未初始化布局"):
        validate_layout(repo, findings)
    report_count("契约检查", 1, 1)
    return findings


def collect_findings(
    repo: Path,
    *,
    full: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    report_progress(
        "契约检查计划",
        "共 5 个检查组：配置、布局与 Agent 控制面；Jot、Proposal 与 Bug；"
        "链接、Change 与 ADR；发布历史；事实文档与 evidence（逐页计数组数量待扫描）",
    )
    report_count("契约检查", 0, 5)
    with progress("契约：配置、布局与 Agent 控制面"):
        for path in managed_symlinks(repo):
            add_finding(
                findings,
                "path.symlink",
                ("本地产物目录为 symlink；允许继续工作，过期清理跳过此目录"
                 if is_local_artifact_root(repo, path) else "MDF-managed paths must not be symbolic links"),
                path.relative_to(repo).as_posix(),
                severity="warning" if is_local_artifact_root(repo, path) else "error",
            )
        manifest = validate_manifest(repo, findings)
        validate_modules(repo, findings)
        validate_layout(repo, findings)
        validate_agents_block(repo, findings)
    report_count("契约检查", 1, 5)

    def objects() -> list[Finding]:
        result: list[Finding] = []
        validate_jots(repo, result)
        for path in iter_object_files(repo, "proposal"):
            validate_object(repo, path, "proposal", result)
        for path in iter_object_files(repo, "bug"):
            validate_object(repo, path, "bug", result)
        return result

    def records() -> list[Finding]:
        result: list[Finding] = []
        validate_links(repo, result)
        validate_changes(repo, result)
        validate_adrs(repo, result)
        validate_record_references(repo, result)
        return result

    def releases() -> list[Finding]:
        result: list[Finding] = []
        validate_changelog(repo, result)
        validate_release_history(repo, manifest, result)
        return result

    def evidence() -> list[Finding]:
        result: list[Finding] = []
        validate_evidence(repo, result, check_staleness=full)
        return result

    findings.extend(collect_parallel([
        ("契约：Jot、Proposal 与 Bug", objects),
        ("契约：链接、Change 与 ADR", records),
        ("契约：发布历史", releases),
        ("契约：事实文档与 evidence", evidence),
    ], label="契约检查", completed_before=1))
    if manifest and manifest.get("state") != "ready":
        add_finding(
            findings,
            "manifest.initializing",
            "manifest 未 ready 前使用 $mdf init 或 $mdf migrate；"
            "符合新仓库条件时可用 $mdf bootstrap",
            ".mdf/manifest.yaml",
        )
    return findings
