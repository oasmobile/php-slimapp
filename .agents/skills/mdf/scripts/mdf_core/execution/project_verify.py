"""suite 运行辅助与 branch 证据路径；verify 入口见 module_verify。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from mdf_core.execution.verify_run import run_verify_command
from mdf_core.lifecycle.delivery_state import safe, read_json, material_root
from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import current_branch, branch_details, unreleased_slug
from mdf_core.execution.verification import SUITES

MAX_PARALLEL = 5


def associated_suites(repo, slug):
    path = material_root(repo, slug) / "suites.json"
    if not path.is_file():
        return None
    data = read_json(safe(repo, path))
    if not isinstance(data, dict) or set(data) != {"suites"}:
        raise MDFError(
            "suites.json 只接受 suites 列表", code="invalid_delivery_suite"
        )
    from mdf_core.execution.verification import parse_suite_names

    return parse_suite_names(data["suites"])


def evidence_path(repo):
    branch = current_branch(repo)
    details = branch_details(branch)
    slug = unreleased_slug(details)
    return safe(
        repo,
        material_root(repo, slug) / "verification-report.json",
    )


def valid_evidence(repo):
    """已落盘且声称通过的 branch 报告；不对照 HEAD。"""
    from mdf_core.execution.module_verify import valid_branch

    return valid_branch(repo)


def _run_one(repo, item, index, total):
    entry = item.get("entry") or item["id"].split(":", 1)[0]
    try:
        detail = run_verify_command(
            repo,
            item["command"],
            label=item["id"],
            index=index,
            total=total,
            timeout=item.get("budget"),
            entry=entry,
            junit=entry in SUITES or item.get("junit", False),
            lint_checks=entry == "lint",
            lint_modules=item.get("lint_modules", [item["module"]] if "module" in item else None),
            coverage_targets=item.get("coverage_targets"),
        )
        return {**item, **detail, "passed": True}
    except MDFError as exc:
        return {
            **item,
            "passed": False,
            "error": exc.code,
            "details": exc.details,
        }


def run_targets(
    repo,
    targets,
    *,
    parallel: bool = False,
    index_base: int = 0,
    grand_total: int | None = None,
):
    """全部运行，不因单项失败中断；每项带 passed 与失败 error/details。"""
    total = grand_total if grand_total is not None else len(targets)
    if not parallel:
        return [
            _run_one(repo, item, index_base + index, total)
            for index, item in enumerate(targets, 1)
        ]
    if len(targets) > MAX_PARALLEL:
        raise MDFError(
            f"并行命令数 {len(targets)} 超过上限 {MAX_PARALLEL}",
            code="too_many_parallel_commands",
            details={"count": len(targets), "max": MAX_PARALLEL},
        )
    results: list[dict | None] = [None] * len(targets)
    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = {
            pool.submit(
                _run_one, repo, item, index_base + index, total
            ): index - 1
            for index, item in enumerate(targets, 1)
        }
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return list(results)
