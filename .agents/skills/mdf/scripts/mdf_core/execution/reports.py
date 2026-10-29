"""suite 运行的 JUnit XML 报告：目录分配、解析与失败判定。"""
import json
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from mdf_core.foundation.errors import MDFError
from mdf_core.execution.run_logs import REPORTS as REPORTS_ROOT, ignored_dir, unique_dir

ENV_NAME = "MDF_REPORT_DIR"


def new_report_dir(repo, entry):
    return unique_dir(ignored_dir(Path(repo) / REPORTS_ROOT), entry)


def _seconds(raw):
    try:
        return float(raw) if raw is not None else None
    except ValueError:
        return None


def _result(element):
    for tag, result in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
        if element.find(tag) is not None:
            return result
    return "passed"


def _collect(path, cases):
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise MDFError(f"测试报告无法解析: {path.name}", code="invalid_test_report") from exc
    suites = [root] if root.tag == "testsuite" else []
    suites += [node for node in root.iter("testsuite") if node is not root]
    for suite in suites:
        for test in suite.findall("testcase"):
            name = test.get("classname") or suite.get("name") or ""
            case = cases.setdefault(name, {"name": name, "tests": []})
            case["tests"].append({
                "name": test.get("name") or "",
                "result": _result(test),
                "time": _seconds(test.get("time")),
            })


def summarize(repo, path, suite):
    """解析报告目录下全部 XML，写入 summary.json 并返回 test case 级汇总。"""
    cases = {}
    files = sorted(Path(path).rglob("*.xml"))
    for file in files:
        _collect(file, cases)
    ordered = []
    for case in cases.values():
        results = {test["result"] for test in case["tests"]}
        times = [test["time"] for test in case["tests"] if test["time"] is not None]
        ordered.append({
            **case,
            "result": "passed" if results == {"passed"} else "failed",
            "time": round(sum(times), 3) if times else None,
        })
    tests = [test for case in ordered for test in case["tests"]]
    totals = {result: sum(test["result"] == result for test in tests)
              for result in ("passed", "failed", "error", "skipped")}
    summary = {"suite": suite, "path": str(Path(path).relative_to(repo)),
               "tests": len(tests), **totals, "cases": ordered}
    (Path(path) / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    compact = {**summary, "cases": [
        {key: case[key] for key in ("name", "result", "time")} for case in ordered
    ]}
    if not files:
        raise MDFError("suite 未产出 JUnit XML 报告", code="missing_test_report", details=compact)
    if not tests:
        raise MDFError("测试报告未包含任何 test", code="empty_test_report", details=compact)
    if len(tests) != totals["passed"]:
        raise MDFError("测试报告含 failure、error 或 skipped", code="test_report_failed",
                       details=compact)
    return compact
