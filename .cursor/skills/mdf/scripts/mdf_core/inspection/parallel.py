"""有限并发执行只读检查，按输入顺序汇总 findings。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import copy_context
from typing import Callable, Sequence

from mdf_core.foundation.errors import Finding
from mdf_core.foundation.progress import progress, report_count


def collect_parallel(
    checks: Sequence[tuple[str, Callable[[], list[Finding]]]],
    *,
    label: str | None = None,
    completed_before: int = 0,
) -> list[Finding]:
    def inspect(check):
        name, run = check
        with progress(name):
            return run()

    if label:
        report_count(label, completed_before, completed_before + len(checks))
    if not checks:
        return []
    results: list[list[Finding]] = [[] for _ in checks]
    with ThreadPoolExecutor(max_workers=min(4, len(checks))) as pool:
        pending = {
            pool.submit(copy_context().run, inspect, check): index
            for index, check in enumerate(checks)
        }
        for completed, future in enumerate(as_completed(pending), start=1):
            index = pending[future]
            results[index] = future.result()
            if label:
                report_count(label, completed_before + completed, completed_before + len(checks),
                             f"，完成 {checks[index][0]}")
    return [finding for result in results for finding in result]
