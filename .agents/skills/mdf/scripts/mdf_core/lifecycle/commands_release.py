import argparse
import json
from pathlib import Path
from typing import Any

from mdf_core.inspection import doctor
from mdf_core.lifecycle.closeout_objects import active_objects
from mdf_core.lifecycle.closeout_stage import apply_closeout, summarize_closeout
from mdf_core.lifecycle.closeout_shape import unreleased_change_slugs, validate_closeout_shape
from mdf_core.lifecycle.closeout_validate import normalize_hotfix_change
from mdf_core.foundation.constants import SCHEMA_VERSION
from mdf_core.foundation.errors import MDFError, emit, has_errors, serialize_findings
from mdf_core.workspace.gitutil import (
    _status_paths,
    branch_details,
    current_branch,
    ensure_clean,
    repo_path,
    require_git_root,
    run,
)
from mdf_core.foundation.paths import ensure_safe_managed_paths, load_manifest
from mdf_core.execution.verification import recorded_suites, repo_verification, required_suite
from mdf_core.foundation.yamlutil import read_frontmatter


def _json_argument(raw: str | None, *, name: str, default: Any) -> Any:
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise MDFError(
            f"{name} must be valid inline JSON", code="invalid_closeout_spec"
        ) from exc


def manifest_verification_commands(manifest: dict[str, Any]) -> list[str]:
    del manifest  # 命令来自 modules.yaml
    raise MDFError(
        "改用 repo_verification(repo).plan('release')",
        code="invalid_verification",
    )


def repo_branch_commands(repo: Path, kind: str) -> list[str]:
    suite = required_suite(kind)
    return [item["command"] for item in repo_verification(repo).plan(suite)]


def reusable_results(repo: Path, commands: list[str]) -> dict[str, Any] | None:
    """已有 branch 报告声称通过且命令序列一致时复用；不对照 HEAD。"""
    from mdf_core.execution.project_verify import evidence_path, valid_evidence

    evidence = valid_evidence(repo)
    if evidence is None:
        return None
    results = evidence.get("results") or []
    if [item.get("command") for item in results] != commands:
        return None
    return {
        "path": str(evidence_path(repo).relative_to(repo)),
        "suites": recorded_suites(evidence),
        "results": [
            {key: item[key] for key in ("command", "exit_code", "log", "report")
             if key in item}
            for item in results
        ],
    }


def written_paths(repo: Path) -> list[str]:
    raw = run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
              cwd=repo, check=False).stdout
    return sorted(_status_paths(raw))


def derive_closeout_spec(
    repo: Path, args: argparse.Namespace
) -> dict[str, Any]:
    details = branch_details(current_branch(repo))
    if details["kind"] not in {"release", "hotfix"}:
        raise MDFError(
            "release closeout 只接受 release/<version> 或 hotfix/<version>",
            code="unsupported_branch",
        )
    mode = details["kind"]
    version = details["version"]
    manifest = load_manifest(repo)
    versioning = manifest.get("versioning")
    previous = (
        versioning.get("latest_release")
        if isinstance(versioning, dict)
        else None
    )
    release_date = args.release_date
    if not isinstance(release_date, str) or not release_date.strip():
        raise MDFError(
            "必须显式提供 --release-date",
            code="invalid_closeout_spec",
        )
    if mode == "release":
        slugs = unreleased_change_slugs(repo, version)
        proposals: set[str] = set()
        fixed: set[str] = set()
        closed: set[str] = set()
        deferred: set[str] = set()
        for slug in slugs:
            metadata, _ = read_frontmatter(
                repo / "changes" / "unreleased" / slug / "CHANGE.md"
            )
            proposals.update(metadata.get("proposals", []))
            fixed.update(metadata.get("fixed", []))
            closed.update(metadata.get("closed", []))
            deferred.update(metadata.get("deferred", []))
        hotfix_change = None
    else:
        raw_hotfix = _json_argument(
            args.hotfix_change_json,
            name="--hotfix-change-json",
            default=None,
        )
        if raw_hotfix is None:
            raise MDFError(
                "hotfix 必须显式提供 --hotfix-change-json",
                code="invalid_closeout_spec",
            )
        hotfix_change = normalize_hotfix_change(raw_hotfix, version)
        proposals = set(hotfix_change["proposals"])
        fixed = set(hotfix_change["fixed"])
        closed = set(hotfix_change["closed"])
        deferred = set(hotfix_change["deferred"])
    records = active_objects(repo)
    fixed.update(
        identifier
        for identifier, (kind, _path, metadata) in records.items()
        if kind == "bug"
        and metadata.get("status") == "closed"
        and metadata.get("fixed_in") == version
    )
    reject_reasons = {
        identifier: metadata.get("reject-reason")
        for identifier in closed
        for _kind, _path, metadata in [records.get(identifier, (None, None, {}))]
        if isinstance(metadata.get("reject-reason"), str)
    }
    if set(reject_reasons) != closed:
        raise MDFError(
            "closed outcome 中的 Bug 必须是带 reject-reason 的 rejected Bug",
            code="invalid_closure",
            details={"missing": sorted(closed - set(reject_reasons))},
        )

    explicit = _json_argument(
        args.closures_json, name="--closures-json", default=None
    )
    if explicit is None:
        closures: list[dict[str, Any]] = []
        closures.extend(
            {
                "id": identifier,
                "resolution": "released",
                "released_in": version,
            }
            for identifier in sorted(proposals)
        )
        closures.extend(
            {"id": identifier, "resolution": "fixed", "fixed_in": version}
            for identifier in sorted(fixed)
        )
        closures.extend(
            {
                "id": identifier,
                "resolution": reject_reasons.get(identifier),
            }
            for identifier in sorted(closed)
        )
        closures.extend(
            {"id": identifier, "resolution": "deferred"}
            for identifier in sorted(deferred)
        )
    else:
        if not isinstance(explicit, list):
            raise MDFError(
                "--closures-json 必须是列表", code="invalid_closeout_spec"
            )
        closures = explicit
    acceptance = _json_argument(
        args.deferred_acceptance_json,
        name="--deferred-acceptance-json",
        default={},
    )
    if not isinstance(acceptance, dict):
        raise MDFError(
            "--deferred-acceptance-json 必须是对象",
            code="invalid_closeout_spec",
        )
    commands = repo_branch_commands(repo, mode)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "expected_branch": f"{mode}/{version}",
        "version": version,
        "previous_version": previous,
        "release_date": release_date,
        "closures": closures,
        "deferred_acceptance": acceptance,
        "hotfix_change": hotfix_change,
        "validation_commands": commands,
    }


def command_release_closeout(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_safe_managed_paths(repo)
    ensure_clean(repo)
    manifest = load_manifest(repo)
    if manifest.get("state") != "ready":
        raise MDFError(
            "release closeout 要求 manifest state 为 ready",
            code="manifest_not_ready",
        )
    pre_findings = doctor.collect_findings(repo, full=True)
    if has_errors(pre_findings):
        raise MDFError(
            "release closeout 要求全量确定性审计零 error",
            code="audit_not_passed",
            details={"findings": serialize_findings(pre_findings)},
        )
    spec = derive_closeout_spec(repo, args)
    context = validate_closeout_shape(repo, spec)
    if args.dry_run:
        emit(
            {
                "ok": True,
                "operation": "release-closeout",
                "dry_run": True,
                "summary": summarize_closeout(repo, context),
            }
        )
        return

    reused = reusable_results(repo, context["validation_commands"])
    if reused is None:
        raise MDFError(
            "release closeout 要求可复用的 verification-report.json"
            "（all_passed 且命令序列一致）；不在 closeout 内执行验证",
            code="verification_report_not_reusable",
        )
    command_results = reused["results"]
    ensure_clean(repo)
    spec["verify_command_results"] = command_results
    context = validate_closeout_shape(repo, spec)
    result = apply_closeout(repo, context)

    post_findings = doctor.collect_findings(repo, full=True)
    if has_errors(post_findings):
        raise MDFError(
            "release closeout 的 post-validation 失败；写入已落在工作树且未提交",
            code="post_validation_failed",
            details={
                "findings": serialize_findings(post_findings),
                "written": written_paths(repo),
            },
        )
    emit(
        {
            "ok": True,
            "operation": "release-closeout",
            "dry_run": False,
            "version": context["version"],
            "release_set": result["slugs"],
            "moves": result["moves"],
            "archived": result["archived"],
            "outcomes": result["outcomes"],
            "semver": result["semver"],
            "rewrites": result["rewrites"],
            "verification": {
                "suites": reused["suites"],
                "commands": context["validation_commands"],
                "results": command_results,
                "reused": reused["path"],
            },
            "audit": {"deterministic": "passed"},
        }
    )
