from pathlib import Path
from typing import Any

from mdf_core.foundation.constants import (
    BASELINES,
    BASELINE_DOC_TYPES,
    SCHEMA_VERSION,
    contains_unreleased_sentinel,
)
from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.foundation.paths import load_manifest, manifest_path, path_stays_in_repo
from mdf_core.foundation.textutil import stable_semver
from mdf_core.foundation.yamlutil import read_frontmatter


def implementation_roots(
    repo: Path, manifest: dict[str, Any], findings: list[Finding]
) -> list[Path]:
    raw_roots = manifest.get("implementation_roots")
    if not isinstance(raw_roots, list) or not raw_roots:
        add_finding(
            findings,
            "manifest.implementation_roots",
            "implementation_roots must be a non-empty path list",
            ".mdf/manifest.yaml",
        )
        return []
    roots: list[Path] = []
    for raw in raw_roots:
        if (
            not isinstance(raw, str)
            or not raw.strip()
            or Path(raw).is_absolute()
        ):
            add_finding(
                findings,
                "manifest.implementation_root",
                "implementation roots must be non-empty repository-relative "
                "paths",
                ".mdf/manifest.yaml",
            )
            continue
        path = (repo / raw).resolve()
        if (
            not path_stays_in_repo(repo, path)
            or not path.is_dir()
            or path.is_symlink()
        ):
            add_finding(
                findings,
                "manifest.implementation_root",
                "implementation root must be a regular in-repository directory",
                raw,
            )
            continue
        if path in roots:
            add_finding(
                findings,
                "manifest.implementation_root_duplicate",
                "implementation roots must not repeat", raw,
            )
            continue
        if any(
            path in other.parents or other in path.parents for other in roots
        ):
            add_finding(
                findings,
                "manifest.implementation_root_overlap",
                "implementation roots must not overlap", raw,
            )
            continue
        roots.append(path)
    return roots


def validate_manifest(
    repo: Path,
    findings: list[Finding],
) -> dict[str, Any] | None:
    path = manifest_path(repo)
    if not path.is_file():
        add_finding(
            findings,
            "manifest.missing",
            "Missing MDF manifest",
            ".mdf/manifest.yaml",
        )
        return None
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        add_finding(
            findings,
            "path.symlink",
            "MDF manifest must be a regular repository file",
            ".mdf/manifest.yaml",
        )
        return None
    try:
        manifest = load_manifest(repo)
    except MDFError as exc:
        add_finding(
            findings, "manifest.invalid", str(exc), ".mdf/manifest.yaml"
        )
        return None
    if manifest.get("schema_version") != SCHEMA_VERSION:
        add_finding(
            findings,
            "manifest.schema",
            f"schema_version must be {SCHEMA_VERSION}；用 $mdf migrate 收敛到当前契约",
            ".mdf/manifest.yaml",
        )
    from mdf_core.workspace.hooks import validate_hooks
    from mdf_core.workspace.merge_policy import config
    try:
        config(manifest)
    except MDFError as exc:
        add_finding(findings, "manifest.closeout", str(exc), ".mdf/manifest.yaml")
    try:
        validate_hooks(manifest)
    except MDFError as exc:
        add_finding(findings, "manifest.hooks", str(exc), ".mdf/manifest.yaml")
    from mdf_core.workspace.project_rules import load_project_rule, validate_rules
    try:
        rules = validate_rules(manifest)
    except MDFError as exc:
        add_finding(findings, "manifest.rules", str(exc), ".mdf/manifest.yaml")
    else:
        for stage in rules:
            try:
                load_project_rule(repo, manifest, stage)
            except MDFError as exc:
                add_finding(findings, "manifest.rules", str(exc), ".mdf/manifest.yaml")
    implementation_roots(repo, manifest, findings)
    if manifest.get("state") not in ("initializing", "ready"):
        add_finding(
            findings,
            "manifest.state",
            "state must be initializing or ready",
            ".mdf/manifest.yaml",
        )
    if "verification" in manifest:
        add_finding(
            findings,
            "manifest.verification_moved",
            "verification 已迁至 .mdf/modules.yaml；请从 manifest 删除 verification"
            "；用 $mdf migrate 收敛到当前契约",
            ".mdf/manifest.yaml",
        )
    versioning = manifest.get("versioning")
    if (
        not isinstance(versioning, dict)
        or versioning.get("strategy") != "semver"
    ):
        add_finding(
            findings,
            "manifest.versioning",
            "versioning.strategy must be semver",
            ".mdf/manifest.yaml",
        )
    elif "latest_release" not in versioning:
        add_finding(
            findings,
            "manifest.latest_release",
            "versioning.latest_release is required",
            ".mdf/manifest.yaml",
        )
    baselines = manifest.get("baselines")
    if not isinstance(baselines, dict):
        add_finding(
            findings,
            "manifest.baselines",
            "baselines must be a mapping",
            ".mdf/manifest.yaml",
        )
        return manifest
    unknown_baselines = sorted(set(baselines) - set(BASELINES))
    if unknown_baselines:
        add_finding(
            findings,
            "baseline.unknown",
            f"Unknown baselines: {', '.join(unknown_baselines)}",
            ".mdf/manifest.yaml",
        )
    resolved = True
    for name in BASELINES:
        entry = baselines.get(name)
        if not isinstance(entry, dict):
            add_finding(
                findings,
                "baseline.missing",
                f"Missing baseline: {name}",
                ".mdf/manifest.yaml",
            )
            resolved = False
            continue
        status = entry.get("status")
        if status not in ("documented", "not_applicable"):
            add_finding(
                findings,
                "baseline.status",
                f"{name}.status must be documented or not_applicable",
                ".mdf/manifest.yaml",
            )
            resolved = False
        elif status == "not_applicable":
            if (
                not isinstance(entry.get("reason"), str)
                or not entry["reason"].strip()
            ):
                add_finding(
                    findings,
                    "baseline.reason",
                    f"{name} requires a reason when not_applicable",
                    ".mdf/manifest.yaml",
                )
                resolved = False
            if "path" in entry:
                add_finding(
                    findings,
                    "baseline.path",
                    f"{name} must not declare path when not_applicable",
                    ".mdf/manifest.yaml",
                )
                resolved = False
        else:
            if "reason" in entry:
                add_finding(
                    findings,
                    "baseline.reason",
                    f"{name} must not declare reason when documented",
                    ".mdf/manifest.yaml",
                )
                resolved = False
            declared_path = entry.get("path")
            if not isinstance(declared_path, str) or not declared_path.strip():
                add_finding(
                    findings,
                    "baseline.path",
                    f"{name} requires a repository-relative path when "
                    "documented",
                    ".mdf/manifest.yaml",
                )
                resolved = False
                continue
            raw_path = Path(declared_path)
            if raw_path.is_absolute():
                add_finding(
                    findings,
                    "baseline.path",
                    f"{name} path must be repository-relative",
                    ".mdf/manifest.yaml",
                )
                resolved = False
                continue
            candidate = (repo / raw_path).resolve()
            try:
                candidate.relative_to(repo)
            except ValueError:
                add_finding(
                    findings,
                    "baseline.path",
                    f"{name} path must stay inside the repository",
                    ".mdf/manifest.yaml",
                )
                resolved = False
                continue
            if not candidate.is_file():
                add_finding(
                    findings,
                    "baseline.document",
                    f"Documented baseline {name} is missing its file",
                    str(declared_path),
                )
                resolved = False
            elif name in BASELINE_DOC_TYPES:
                try:
                    metadata, _ = read_frontmatter(candidate)
                except MDFError as exc:
                    add_finding(
                        findings,
                        "baseline.frontmatter",
                        f"{name} baseline is invalid: {exc}",
                        declared_path,
                    )
                    resolved = False
                else:
                    expected_type = BASELINE_DOC_TYPES[name]
                    if metadata.get("doc_type") != expected_type:
                        add_finding(
                            findings,
                            "baseline.doc_type",
                            f"{name} baseline requires doc_type "
                            f"{expected_type}",
                            declared_path,
                        )
                        resolved = False
    if manifest.get("state") == "ready" and not resolved:
        add_finding(
            findings,
            "manifest.not_ready",
            "state ready 要求全部基线已解决",
            ".mdf/manifest.yaml",
        )
    latest_release = (
        versioning.get("latest_release")
        if isinstance(versioning, dict)
        else None
    )
    if latest_release is not None and stable_semver(latest_release) is None:
        add_finding(
            findings,
            "manifest.latest_release",
            "versioning.latest_release 必须为 null 或稳定 SemVer",
            ".mdf/manifest.yaml",
        )
    if contains_unreleased_sentinel(manifest):
        add_finding(
            findings,
            "version.sentinel_scope",
            "manifest 中禁止使用 unreleased",
            ".mdf/manifest.yaml",
        )
    return manifest
