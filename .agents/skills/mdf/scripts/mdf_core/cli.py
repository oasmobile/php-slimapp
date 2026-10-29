import argparse
import json
import sys
import traceback

from mdf_core.commands_misc import (
    command_archive,
    command_branch,
    command_doctor,
    command_info,
    command_init,
    command_make_id,
    command_make_jot_id,
    command_semver,
    command_validate,
)
from mdf_core.inspection.audit import command_audit
from mdf_core.inspection.doc_size import command_prose_check
from mdf_core.lifecycle.commands_release import command_release_closeout
from mdf_core.foundation.errors import MDFError
from mdf_core.execution.run_logs import RunLog, command_run
from mdf_core.workspace.gitflow import command_finish_gitflow, command_start
from mdf_core.workspace.upgrade import DEFAULT_SKILL_SOURCE, command_upgrade


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mars Development Flow deterministic core"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    from mdf_core.documents.bug_close import command_bug_close

    bug = subparsers.add_parser("bug")
    bug_actions = bug.add_subparsers(dest="action", required=True)
    bug_close = bug_actions.add_parser("close")
    bug_close.add_argument("bug_id")
    bug_close.add_argument("--repo", required=True)
    bug_close.add_argument("--fixed-in", required=True)
    bug_close.set_defaults(func=command_bug_close)

    info = subparsers.add_parser("info")
    info.set_defaults(func=command_info)

    from mdf_core.workspace.project_rules import STAGES as RULE_STAGES, command_project_rules
    rules = subparsers.add_parser("project-rules")
    rules.add_argument("--repo", required=True)
    rules.add_argument("--stage", choices=RULE_STAGES, required=True)
    rules.set_defaults(func=command_project_rules)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--repo", required=True)
    doctor.set_defaults(func=command_doctor)

    from mdf_core.workspace.git_ops import command_merge_no_ff, command_prepare_git

    prepare_git = subparsers.add_parser("prepare-git")
    prepare_git.add_argument("--repo", required=True)
    prepare_git.set_defaults(func=command_prepare_git)

    merge = subparsers.add_parser("merge-no-ff")
    merge.add_argument("--repo", required=True)
    merge.add_argument("--commit", required=True)
    merge.set_defaults(func=command_merge_no_ff)

    init = subparsers.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--latest-release", required=True)
    init.add_argument("--baseline", action="append", default=[], required=True)
    for name in ("lint", "build", "quick", "smoke", "release"):
        init.add_argument(f"--{name}", required=True)
    init.add_argument("--budget", action="append", default=[])
    init.add_argument(
        "--implementation-root", action="append", default=[]
    )
    init.set_defaults(func=command_init)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--repo", required=True)
    validate.add_argument(
        "--level", choices=("basic", "strict"), default="basic"
    )
    validate.set_defaults(func=command_validate)

    audit = subparsers.add_parser("fact-audit")
    audit.add_argument("--repo", required=True)
    audit.add_argument(
        "--scope", choices=("full", "branch", "paths"), default=None
    )
    audit.add_argument("--base")
    audit.add_argument("--against")
    audit.add_argument("--quick", action="store_true")
    audit.add_argument("--implementation-path", action="append", default=[])
    audit.add_argument("--document-path", action="append", default=[])
    audit.set_defaults(func=command_audit)

    from mdf_core.reviewing.fact_report import command_fact_report_check
    fact_report = subparsers.add_parser("fact-audit-report-check")
    fact_report.add_argument("--context-file", required=True)
    fact_report.add_argument("--report-file", required=True)
    fact_report.set_defaults(func=command_fact_report_check)

    prose = subparsers.add_parser("prose-check")
    prose.add_argument("--repo", required=True)
    prose.add_argument("--path", action="append", default=[])
    prose.set_defaults(func=command_prose_check)

    make_id = subparsers.add_parser("make-id")
    make_id.add_argument(
        "--type", choices=("proposal", "bug"), required=True
    )
    make_id.add_argument("--slug", required=True, action="append")
    make_id.add_argument("--repo")
    make_id.set_defaults(func=command_make_id)

    make_jot_id = subparsers.add_parser("make-jot-id")
    make_jot_id.set_defaults(func=command_make_jot_id)

    branch = subparsers.add_parser("branch")
    branch.add_argument("--repo")
    branch.add_argument("--name")
    branch.set_defaults(func=command_branch)

    from mdf_core.inspection.push_audit import command_audit_push
    audit_push = subparsers.add_parser("audit-push")
    for name in ("repo", "branch", "before", "after"):
        audit_push.add_argument(f"--{name}", required=True)
    audit_push.add_argument("--evidence-file")
    audit_push.add_argument("--collect-evidence", action="store_true")
    audit_push.set_defaults(func=command_audit_push)

    from mdf_core.reviewing.context import command_context
    review_context = subparsers.add_parser("review-context")
    review_context.add_argument("--repo", required=True)
    review_context.add_argument("--source")
    for name in ("head", "policy-ref", "against"):
        review_context.add_argument(f"--{name}")
    review_context.add_argument("--review-base")
    review_context.add_argument("--previous-report")
    review_context.set_defaults(func=command_context)

    from mdf_core.reviewing.report import command_report_check
    report_check = subparsers.add_parser("review-report-check")
    report_check.add_argument("--context-file", required=True)
    report_check.add_argument("--report-file", required=True)
    report_check.set_defaults(func=command_report_check)

    semver = subparsers.add_parser("semver-check")
    semver.add_argument("--previous", required=True)
    semver.add_argument("--candidate", required=True)
    semver.add_argument("--categories")
    semver.add_argument("--breaking", action="store_true")
    semver.set_defaults(func=command_semver)

    archive = subparsers.add_parser("archive")
    archive.add_argument("--repo", required=True)
    archive.add_argument("--epoch", required=True)
    archive.add_argument("--dry-run", action="store_true")
    archive.set_defaults(func=command_archive)

    closeout = subparsers.add_parser("release-closeout")
    closeout.add_argument("--repo", required=True)
    closeout.add_argument("--release-date")
    closeout.add_argument("--closures-json")
    closeout.add_argument("--deferred-acceptance-json")
    closeout.add_argument("--hotfix-change-json")
    closeout.add_argument("--dry-run", action="store_true")
    closeout.set_defaults(func=command_release_closeout)

    start = subparsers.add_parser("start")
    start.add_argument("--repo", required=True)
    start.add_argument(
        "--kind",
        choices=("feature", "bugfix", "release", "hotfix", "adhoc"),
        required=True,
    )
    start.add_argument("--name")
    start.add_argument("--work")
    start.add_argument("--manual", action="store_true")
    start.add_argument("--proposal")
    start.add_argument("--bug")
    start.add_argument("--objectives-file")
    start.add_argument("--version")
    start.add_argument("--qa", type=int)
    start.add_argument("--dev", type=int)
    start.add_argument("--reviewers", type=int)
    from mdf_core.lifecycle.roster import add_named_roster_argument, add_strategy_arguments
    add_named_roster_argument(start)
    add_strategy_arguments(start)
    start.set_defaults(func=command_start)

    from mdf_core.lifecycle.adhoc import command_status as command_adhoc_status
    adhoc_status = subparsers.add_parser("adhoc-status")
    adhoc_status.add_argument("--repo", required=True)
    adhoc_status.add_argument("--slug")
    adhoc_status.add_argument("--source")
    adhoc_status.set_defaults(func=command_adhoc_status)

    from mdf_core.documents.list_objects import command_list
    from mdf_core.documents.tree_view import command_tree
    from mdf_core.documents.prp_split import command_split
    from mdf_core.lifecycle.delivery import command_delivery
    from mdf_core.lifecycle.delivery_state import STAGES

    tree_parser = subparsers.add_parser("tree")
    tree_parser.add_argument("--repo", required=True)
    tree_parser.add_argument("--depth", type=int, default=3)
    tree_parser.set_defaults(func=command_tree)

    listing = subparsers.add_parser("list")
    listing.add_argument("--repo", required=True)
    listing.add_argument("--type", choices=("proposal", "bug"))
    listing.add_argument("--status", action="append", default=[])
    listing.add_argument("--milestone")
    listing.add_argument("--severity")
    listing.set_defaults(func=command_list)

    split = subparsers.add_parser("prp-split")
    split.add_argument("--repo", required=True)
    split.add_argument("--spec-file", required=True)
    split.add_argument("--dry-run", action="store_true")
    split.set_defaults(func=command_split)

    from mdf_core.documents.prp_format import command_prp_format
    prp_format = subparsers.add_parser("prp-format")
    prp_format.add_argument("action", choices=("preview", "ready", "draft"))
    prp_format.add_argument("--repo", required=True)
    prp_format.add_argument("--proposal", required=True)
    prp_format.add_argument("--confirmed", action="store_true")
    prp_format.set_defaults(func=command_prp_format)

    delivery = subparsers.add_parser("delivery")
    delivery.add_argument(
        "action",
        choices=("status", "check", "record", "roster-join", "roster"),
    )
    delivery.add_argument("--repo", required=True)
    delivery.add_argument("--stage", choices=(*STAGES, "finish"))
    delivery.add_argument("--summary")
    delivery.add_argument("--policy-file")
    delivery.add_argument("--test-approval")
    delivery.add_argument("--qa-branch")
    delivery.add_argument("--dev-branch")
    add_strategy_arguments(delivery)
    delivery.set_defaults(func=command_delivery)

    from mdf_core.workspace.planning import command_planning
    planning = subparsers.add_parser("planning")
    planning.add_argument("action", choices=("ensure", "land"))
    planning.add_argument("--repo", required=True)
    planning.set_defaults(func=command_planning)

    from mdf_core.workspace.to_target import command_to
    to_cmd = subparsers.add_parser("to")
    to_cmd.add_argument("--repo", required=True)
    to_cmd.add_argument("--target", required=True)
    to_cmd.set_defaults(func=command_to)

    from mdf_core.workspace.dev_pr import command_dev_pr
    dev_pr = subparsers.add_parser("dev-pr")
    dev_pr.add_argument("--repo", required=True)
    dev_pr.add_argument("--slug")
    dev_pr.set_defaults(func=command_dev_pr)

    from mdf_core.workspace.sync import command_sync
    sync_cmd = subparsers.add_parser("sync")
    sync_cmd.add_argument("--repo", required=True)
    sync_cmd.add_argument("--confirm")
    sync_cmd.add_argument("--pr", action="store_true", help="通过 PR/MR 同步受保护 trunk 的本地增量")
    sync_cmd.set_defaults(func=command_sync)

    from mdf_core.integrations.codewiki_runtime import command_codewiki_runtime
    runtime = subparsers.add_parser("codewiki-runtime")
    runtime.add_argument("--directory", default="~/.local/share/codewiki")
    runtime.set_defaults(func=command_codewiki_runtime)

    from mdf_core.workspace.worktree_check import command_worktree_check
    worktree = subparsers.add_parser("worktree-check")
    worktree.add_argument("--repo", required=True)
    worktree.add_argument("--owner", required=True)
    worktree.add_argument("--role", choices=("owner", "qa", "dev"), required=True)
    worktree.add_argument("--index", type=int, default=1)
    worktree.add_argument("--design-commit")
    worktree.add_argument("--expected-head")
    worktree.add_argument("--handoff", action="store_true")
    worktree.set_defaults(func=command_worktree_check)

    from mdf_core.execution.module_verify import command_verify

    verify = subparsers.add_parser("verify")
    verify.add_argument("target", nargs="?", help="scope 或 named suite 名")
    verify.add_argument("--repo", required=True)
    verify.add_argument(
        "--scope",
        choices=("smart", "branch", "named"),
    )
    verify.add_argument(
        "--suites",
        help="named 范围：逗号分隔的 suite 名（固定入口、可选 coverage 或 named）",
    )
    verify.add_argument(
        "--module",
        action="append",
        default=[],
        help="smart 目标 module；可重复",
    )
    verify.add_argument(
        "--paths",
        action="append",
        default=[],
        help="改动路径，用于推断 smart module",
    )
    verify.add_argument(
        "--test",
        action="append",
        default=[],
        help="smart 额外 test/testcase 命令（Agent+Jev 选题后传入）",
    )
    verify.set_defaults(func=command_verify)

    pull = subparsers.add_parser("pr")
    pull.add_argument("--repo", required=True)
    pull.add_argument("--source")
    pull.set_defaults(func=command_finish_gitflow, phase="pr")

    finish = subparsers.add_parser("finish-gitflow")
    finish.add_argument("--repo", required=True)
    finish.add_argument("--source")
    finish.set_defaults(func=command_finish_gitflow)

    from mdf_core.workspace.finish_hook import command_pre_gitflow_finish
    finish_hook = subparsers.add_parser("pre-gitflow-finish")
    finish_hook.add_argument("--repo", required=True)
    finish_hook.add_argument("--after")
    finish_hook.set_defaults(func=command_pre_gitflow_finish)

    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("--repo", required=True)
    upgrade.add_argument("--source", default=DEFAULT_SKILL_SOURCE)
    upgrade.add_argument("--dry-run", action="store_true")
    upgrade.add_argument("--expected-commit")
    upgrade.set_defaults(func=command_upgrade)

    run = subparsers.add_parser("run")
    run.add_argument("--repo", required=True)
    run.add_argument("--name", default="run")
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(func=command_run)

    from mdf_core.integrations.integrate import command_integrate

    integrate = subparsers.add_parser("integrate")
    integrate.add_argument(
        "action",
        choices=("init", "peer", "send", "poll", "listen", "status"),
    )
    integrate.add_argument("--repo", required=True)
    integrate.add_argument("--name")
    integrate.add_argument("--target")
    integrate.add_argument("--token")
    integrate.add_argument("--to")
    integrate.add_argument(
        "--kind",
        choices=("ping", "courtesy", "ack", "heartbeat", "send", "bug-request", "end"),
    )
    integrate.add_argument("--reply-to")
    integrate.add_argument("--body")
    integrate.add_argument("--observed")
    integrate.add_argument("--expected")
    integrate.add_argument("--repro")
    integrate.add_argument("--impact")
    integrate.add_argument("--timeout", type=float)
    integrate.add_argument("--wait", type=float)
    integrate.add_argument("--bind", default="127.0.0.1:8765")
    integrate.set_defaults(func=command_integrate)
    return parser


def _failure(code: str, message: str, details, log: RunLog) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error": code,
                "message": message,
                "details": details,
                "log": str(log.path),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 1


def _run(argv: list[str], log: RunLog) -> int:
    args = build_parser().parse_args(argv)
    args.log_path = log.path
    try:
        args.func(args)
        return 0
    except MDFError as exc:
        return _failure(exc.code, str(exc), exc.details, log)
    except (OSError, UnicodeError) as exc:
        traceback.print_exc(file=sys.stderr)
        return _failure("operation_failed", str(exc), None, log)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        traceback.print_exc(file=sys.stderr)
        return _failure("internal_error", str(exc), None, log)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    log = RunLog(argv)
    code = 1
    with log:
        try:
            code = _run(argv, log)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else int(exc.code is not None)
            raise
        finally:
            log.finish(code)
    return code
