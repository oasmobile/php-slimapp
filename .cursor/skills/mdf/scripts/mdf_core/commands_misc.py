import argparse
from pathlib import Path
from typing import Any

from mdf_core.inspection import doctor
from mdf_core.documents.archive import archive_plan
from mdf_core.foundation.constants import PROTOCOL_VERSION, SCHEMA_VERSION, TOOL_VERSION
from mdf_core.foundation.digests import text_diff
from mdf_core.foundation.errors import Finding, MDFError, emit, has_errors, serialize_findings
from mdf_core.workspace.gitutil import (
    branch_details,
    current_branch,
    ensure_clean,
    git_is_clean,
    git_root,
    repo_path,
    require_planning,
    require_git_root,
)
from mdf_core.documents.proposals import new_prp_ids
from mdf_core.foundation.progress import ProgressPlan
from mdf_core.workspace.init_repo import init_files, parse_baselines, write_files
from mdf_core.workspace.gitflow import require_master_default
from mdf_core.documents.moves import apply_moves_and_rewrites, describe_moves, describe_rewrites, replacement_plan
from mdf_core.foundation.paths import (
    ensure_safe_managed_paths,
    load_manifest,
    manifest_path,
    path_stays_in_repo,
    relative,
)
from mdf_core.foundation.semver import bump_kind, required_bump
from mdf_core.foundation.textutil import is_object_id_slug, new_short_id, slugify, stable_semver


def command_info(_: argparse.Namespace) -> None:
    emit(
        {
            "ok": True,
            "tool": "mdf",
            "tool_version": TOOL_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "schema_version": SCHEMA_VERSION,
        }
    )


def command_doctor(args: argparse.Namespace) -> None:
    plan = ProgressPlan("doctor", ("识别仓库", "检查 MDF 契约", "汇总 Git 与初始化状态"),
                        groups=("契约检查", "事实文档"))
    with plan.stage(1):
        repo = repo_path(args.repo)
        root = git_root(repo)
        initialized = manifest_path(repo).is_file()
    with plan.stage(2):
        if initialized:
            findings = doctor.collect_findings(repo, full=True)
        else:
            findings = doctor.collect_uninitialized_findings(repo)
    with plan.stage(3):
        branch: dict[str, Any] | None = None
        branch_error: str | None = None
        if root == repo:
            try:
                branch = branch_details(current_branch(repo))
            except MDFError as exc:
                branch_error = str(exc)
                findings.append(
                    Finding(
                        "branch.invalid",
                        branch_error,
                        severity="error",
                    )
                )
        payload = {
            "ok": True,
            "operation": "doctor",
            "repo": str(repo),
            "git_root": str(root) if root else None,
            "is_git_root": root == repo,
            "clean": git_is_clean(repo) if root == repo else None,
            "branch": branch,
            "branch_error": branch_error,
            "initialized": initialized,
            "state": None,
            "normal_workflows_allowed": False,
            "findings": serialize_findings(findings),
        }
        if initialized:
            try:
                payload["state"] = load_manifest(repo).get("state")
            except MDFError:
                payload["state"] = "invalid"
            payload["normal_workflows_allowed"] = (
                payload["state"] == "ready"
                and not any(
                    finding.severity == "error"
                    and finding.code not in {"evidence.stale", "generated.stale"}
                    for finding in findings
                )
            )
    emit(payload)


def command_init(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    require_master_default(repo)
    ensure_safe_managed_paths(repo)
    baselines = parse_baselines(args.baseline)
    from mdf_core.execution.verification import ENTRIES, parse_budgets, validate_verification
    raw_verification = {name: getattr(args, name) for name in ENTRIES}
    budgets = parse_budgets(args.budget)
    if budgets:
        raw_verification["budgets"] = budgets
    verification = validate_verification(raw_verification).config()
    implementation_roots = list(args.implementation_root) or ["src"]
    root_paths: list[Path] = []
    for raw in implementation_roots:
        candidate = Path(raw)
        target = (repo / candidate).resolve()
        if (
            not raw.strip()
            or candidate.is_absolute()
            or not path_stays_in_repo(repo, target)
            or target == repo
            or target in root_paths
            or any(
                target in item.parents or item in target.parents
                for item in root_paths
            )
        ):
            raise MDFError(
                "--implementation-root must use unique in-repository "
                "directories",
                code="invalid_implementation_root",
            )
        root_paths.append(target)
    existing_manifest = manifest_path(repo).is_file()
    latest_release: str | None
    if args.latest_release == "none":
        latest_release = None
    elif stable_semver(args.latest_release) is not None:
        latest_release = args.latest_release
    else:
        raise MDFError(
            "--latest-release must be a stable SemVer or none",
            code="invalid_latest_release",
        )
    files = init_files(
        repo,
        baselines,
        latest_release=latest_release,
        verification=verification,
        implementation_roots=implementation_roots,
    )
    create = [
        relative(repo, path) for path in sorted(files) if not path.exists()
    ]
    update = [relative(repo, path) for path in sorted(files) if path.exists()]
    plan = {
        "mode": "update" if existing_manifest else "initialization",
        "create": create,
        "update": update,
        "state": "initializing",
        "latest_release": latest_release,
        "baselines": baselines,
        "verification": verification,
        "implementation_roots": implementation_roots,
        "files": [
            {
                "path": relative(repo, path),
                "action": "update" if path.exists() else "create",
                "diff": text_diff(
                    relative(repo, path),
                    (
                        path.read_text(encoding="utf-8")
                        if path.exists() and path.is_file()
                        else ""
                    ),
                    content,
                ),
            }
            for path, content in sorted(
                files.items(),
                key=lambda item: relative(repo, item[0]),
            )
        ],
        "next": (
            "按调用 intent 完成核对与校验，取得启用确认后改为 ready，"
            "再次运行 strict validation 并提交就绪结果。"
        ),
    }
    write_files(
        files,
        replace_allowed={
            path
            for path in (repo / "AGENTS.md", manifest_path(repo))
            if path.exists()
        },
    )
    emit(
        {
            "ok": True,
            "operation": "init",
            "repo": str(repo),
            "plan": plan,
        }
    )


def validation_payload(repo: Path, level: str) -> tuple[dict[str, Any], int]:
    plan = ProgressPlan("validate", (f"{level} 契约校验",), groups=("契约检查", "事实文档"))
    with plan.stage(1):
        findings = doctor.collect_findings(repo, full=level == "strict")
    payload = {
        "ok": not has_errors(findings),
        "operation": "validate",
        "level": level,
        "repo": str(repo),
        "finding_count": len(findings),
        "findings": serialize_findings(findings),
    }
    return payload, 0 if not has_errors(findings) else 2


def command_validate(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    payload, exit_code = validation_payload(repo, args.level)
    emit(payload)
    if exit_code:
        raise SystemExit(exit_code)


def command_make_id(args: argparse.Namespace) -> None:
    slugs = [slugify(value) for value in args.slug]
    if len(set(slugs)) != len(slugs) or any(is_object_id_slug(value) for value in slugs):
        raise MDFError("slug 不得重复或与对象 ID 同形", code="slug_is_id")
    if args.type == "proposal":
        if args.repo is None:
            raise MDFError("Proposal ID 需要 --repo", code="missing_argument")
        repo = repo_path(args.repo)
        require_git_root(repo)
        require_planning(repo)
        ids = new_prp_ids(repo, len(slugs))
    else:
        ids = [f"bug-{new_short_id()}" for _ in slugs]
    items = [{"type": args.type, "id": identifier, "filename": f"{identifier}-{slug}.md"}
             for identifier, slug in zip(ids, slugs)]
    emit({"ok": True, "operation": "make-id", **(items[0] if len(items) == 1 else {"items": items})})


def command_make_jot_id(_: argparse.Namespace) -> None:
    emit(
        {
            "ok": True,
            "operation": "make-jot-id",
            "id": f"jot-{new_short_id()}",
        }
    )


def command_branch(args: argparse.Namespace) -> None:
    name = args.name
    if name is None:
        if args.repo is None:
            raise MDFError(
                "branch requires --repo or --name", code="missing_argument"
            )
        name = current_branch(repo_path(args.repo))
    emit({"ok": True, "operation": "branch", **branch_details(name)})


def command_semver(args: argparse.Namespace) -> None:
    previous = stable_semver(args.previous)
    candidate = stable_semver(args.candidate)
    if previous is None or candidate is None:
        raise MDFError(
            "Previous and candidate must be stable MAJOR.MINOR.PATCH versions",
            code="invalid_semver",
        )
    raw_categories: list[str] = (
        [part.strip() for part in args.categories.split(",")]
        if args.categories
        else []
    )
    categories = {item for item in raw_categories if item}
    allowed = {
        "Added",
        "Changed",
        "Deprecated",
        "Removed",
        "Fixed",
        "Security",
        "none",
    }
    unknown = sorted(categories - allowed)
    if unknown:
        raise MDFError(
            f"Unknown changelog categories: {', '.join(unknown)}",
            code="bad_category",
        )
    if not categories:
        categories = {"none"}
    if "none" in categories and len(categories) > 1:
        raise MDFError(
            "release_notes none must be exclusive", code="mixed_none"
        )
    actual = bump_kind(previous, candidate)
    removed_without_declaration = "Removed" in categories and not args.breaking
    effective_breaking = args.breaking
    required = required_bump(previous, categories, effective_breaking)
    rank = {"patch": 1, "minor": 2, "major": 3}
    allowed_bump = (
        not removed_without_declaration and rank[actual] >= rank[required]
    )
    payload = {
        "ok": allowed_bump,
        "operation": "semver-check",
        "previous": args.previous,
        "candidate": args.candidate,
        "categories": sorted(categories),
        "breaking": effective_breaking,
        "breaking_declared": args.breaking,
        "removed_requires_breaking": removed_without_declaration,
        "required_bump": required,
        "actual_bump": actual,
    }
    emit(payload)
    if not allowed_bump:
        raise SystemExit(2)


def command_archive(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_safe_managed_paths(repo)
    load_manifest(repo)
    ensure_clean(repo)
    input_findings = doctor.collect_findings(repo, full=True)
    if has_errors(input_findings):
        raise MDFError(
            "Archive input does not pass strict validation",
            code="invalid_object",
            details={"findings": serialize_findings(input_findings)},
        )
    moves, rewrites = archive_plan(repo, args.epoch)
    move_details = describe_moves(repo, moves)
    rewrite_details = describe_rewrites(repo, rewrites)
    payload = {
        "ok": True,
        "operation": "archive",
        "dry_run": args.dry_run,
        "epoch": args.epoch,
        "external_links": "not_rewritten",
        "moves": move_details,
        "rewrites": [relative(repo, path) for path in sorted(rewrites)],
        "rewrite_details": rewrite_details,
        "validation": {"level": "strict", "finding_count": 0},
    }
    if not args.dry_run:
        apply_moves_and_rewrites(moves, rewrites)
        post_findings = doctor.collect_findings(repo, full=True)
        if has_errors(post_findings):
            raise MDFError(
                "Archive post-validation failed; leave the git worktree for "
                "manual inspection",
                code="post_validation_failed",
                details={"findings": serialize_findings(post_findings)},
            )
    emit(payload)
