"""所有 lint 入口共用的代码规模检查；文档规模由 fact audit 检查。"""
import json

from mdf_core.execution.modules import load_modules, match
from mdf_core.foundation.errors import MDFError, serialize_findings
from mdf_core.foundation.paths import path_stays_in_repo
from mdf_core.inspection.code_size import code_size_findings, package_size_findings
from mdf_core.workspace.gitutil import run


def summarize_lint(repo, directory, modules=None, *, command_passed=True):
    config = load_modules(repo)
    tracked = [repo / path for path in run(["git", "ls-files", "-z"], cwd=repo).stdout.split("\0") if path]
    tracked = [path for path in tracked if path_stays_in_repo(repo, path)]
    selected = tracked
    if modules is not None:
        patterns = [pattern for name in modules for pattern in config.get(name).sourceset]
        selected = [path for path in tracked if any(match(path.relative_to(repo).as_posix(), pattern)
                                                    for pattern in patterns)]
    findings = code_size_findings(repo, selected, config=config)
    findings += package_size_findings(repo, tracked, scope_paths=selected, config=config)
    summary = {"all_passed": not findings and command_passed, "structure_passed": not findings,
               "command_passed": command_passed, "findings": serialize_findings(findings)}
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not summary["all_passed"]:
        raise MDFError("lint 检查失败", code="lint_failed", details=summary)
    return summary
