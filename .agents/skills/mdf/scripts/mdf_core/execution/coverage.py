"""可选 coverage 配置与项目统一 JSON 报告的确定性判定。"""
import json
import math
from fractions import Fraction
from pathlib import Path

from mdf_core.foundation.errors import MDFError


def parse_coverage(raw, label):
    if not isinstance(raw, dict) or set(raw) != {"command", "targets"}:
        raise MDFError(f"{label} 必须含 command 与 targets", code="invalid_coverage")
    command, targets = raw["command"], raw["targets"]
    if not isinstance(command, str) or not command.strip():
        raise MDFError(f"{label}.command 必须非空", code="invalid_coverage")
    if not isinstance(targets, dict) or not targets:
        raise MDFError(f"{label}.targets 必须是非空 mapping", code="invalid_coverage")
    for metric, target in targets.items():
        if (not isinstance(metric, str) or not metric.strip()
                or type(target) not in (int, float) or not 0 <= target <= 100
                or not math.isfinite(target)):
            raise MDFError(f"{label}.targets 需要非空 metric 与 0–100 的有限数", code="invalid_coverage")
    return {"command": command.strip(), "targets": dict(targets)}


def summarize_coverage(directory: Path, targets, *, command_passed=True):
    path = directory / "coverage.json"
    try:
        if path.is_symlink():
            raise ValueError("coverage.json 不得为 symlink")
        data = json.loads(path.read_text(encoding="utf-8"))
        metrics = data["metrics"]
        if not isinstance(metrics, dict):
            raise ValueError("metrics 必须是 mapping")
        results = {}
        for name, target in targets.items():
            counts = metrics[name]
            covered, total = counts["covered"], counts["total"]
            if type(covered) is not int or type(total) is not int or not 0 <= covered <= total or total <= 0:
                raise ValueError(f"{name} 需要 0 <= covered <= total 且 total > 0 的整数")
            results[name] = {"covered": covered, "total": total, "target": target,
                             "actual": covered * 100 / total,
                             "passed": covered * 100 >= Fraction(str(target)) * total}
        summary = {"metrics": results, "command_passed": command_passed,
                   "all_passed": command_passed and all(item["passed"] for item in results.values())}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        summary = {"all_passed": False, "error": str(exc)}
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not summary["all_passed"]:
        raise MDFError("coverage 报告无效或未达到 target", code="coverage_failed", details=summary)
    return summary
