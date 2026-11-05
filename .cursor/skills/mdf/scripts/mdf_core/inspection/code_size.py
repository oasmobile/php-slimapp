"""源代码与测试源码规模的测量及硬限制；配置、数据与文档不参与代码计数。"""
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from mdf_core.execution.modules import ModulesConfig, SizeLimits, path_ignored
from mdf_core.foundation.errors import Finding
from mdf_core.foundation.paths import relative

SOURCE_SUFFIXES = {
    ".py", ".pyi", ".sh", ".bash", ".zsh", ".js", ".jsx", ".mjs", ".cjs",
    ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte", ".go", ".rs", ".java",
    ".kt", ".kts", ".scala", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp",
    ".cs", ".fs", ".fsx", ".vb", ".swift", ".m", ".mm", ".rb", ".php",
    ".pl", ".pm", ".r", ".lua", ".ex", ".exs", ".erl", ".hrl", ".hs",
    ".dart", ".clj", ".cljs", ".cljc", ".groovy", ".jl", ".sql",
    ".css", ".scss", ".sass", ".less",
}


def is_source(path: Path) -> bool:
    return path.suffix.lower() in SOURCE_SUFFIXES


def _source_files(repo: Path, paths: Iterable[Path], config: ModulesConfig | None) -> list[Path]:
    return sorted(path for path in set(paths) if is_source(path) and path.is_file() and not path.is_symlink()
                  and not (config and config.is_ignored(relative(repo, path))))


def _policies(repo: Path, paths: list[Path], config: ModulesConfig | None) -> list[tuple[str, SizeLimits]]:
    return config.size_policies([relative(repo, path) for path in paths]) if config is not None else [("", SizeLimits())]


def code_size_findings(repo: Path, paths: Iterable[Path], *,
                       config: ModulesConfig | None = None) -> list[Finding]:
    findings = []
    for path in _source_files(repo, paths, config):
        count = len(path.read_text(encoding="utf-8").splitlines())
        for module, limits in _policies(repo, [path], config):
            if count > limits.max_file_lines:
                prefix = f"module {module}: " if module else ""
                findings.append(Finding(
                    "code.size",
                    f"{prefix}源代码 {count} 行，超过限制 {limits.max_file_lines}；"
                    f"必须按职责与设计模式拆分，每个结果最多 {limits.target(limits.max_file_lines)} 行",
                    relative(repo, path),
                ))
    return findings


def is_test_source(path: Path) -> bool:
    return (bool({"test", "tests", "__tests__"}.intersection(path.parts[:-1]))
            or path.name.startswith("test_")
            or path.stem.endswith(("_test", "Test", "Tests"))
            or ".test." in path.name or ".spec." in path.name)


def package_size_findings(repo: Path, paths: Iterable[Path], *,
                          scope_paths: Iterable[Path] | None = None,
                          config: ModulesConfig | None = None) -> list[Finding]:
    """按完整目录同类成员计数，逐项满足成员适用的全部 module 配置。"""
    touched = None if scope_paths is None else {
        path.parent for path in scope_paths if is_source(path)
        and not (config and config.is_ignored(relative(repo, path)))
    }
    groups = defaultdict(list)
    for path in _source_files(repo, paths, config):
        if touched is None or path.parent in touched:
            groups[path.parent, is_test_source(path.relative_to(repo))].append(path)
    findings = []
    for (package, tests), members in sorted(groups.items()):
        for module, limits in _policies(repo, members, config):
            count = sum(not path_ignored(relative(repo, p), config.get(module)) for p in members) if module else len(members)
            if count > limits.max_package_files:
                prefix = f"module {module}: " if module else ""
                findings.append(Finding(
                    "package.size",
                    f"{prefix}package 的{'测试' if tests else '实现'}文件 {count} 个，"
                    f"超过 {limits.max_package_files}；必须按职责与设计模式拆分，"
                    f"每个结果同类直属文件最多 {limits.target(limits.max_package_files)} 个",
                    relative(repo, package),
                ))
    return findings


def code_size_measurements(line_counts: dict[str, int], all_paths: list[str],
                           config: ModulesConfig) -> dict:
    """只返回工具实测与两类阈值；拆分目标是否适用由审查上下文确定。"""
    eligible = {name for name in all_paths if is_source(Path(name)) and not config.is_ignored(name)}
    selected = {name: count for name, count in line_counts.items() if name in eligible}

    def record(path, module, value, limit, limits, **extra):
        target = limits.target(limit)
        return {"path": path, "module": module, "value": value, "limit": limit,
                "split_target": target, "within_limit": value <= limit,
                "within_split_target": value <= target, **extra}

    files = [record(name, module, count, limits.max_file_lines, limits)
             for name, count in sorted(selected.items())
             for module, limits in config.size_policies([name])]
    touched = {Path(name).parent for name in selected}
    groups = defaultdict(list)
    for name in sorted(eligible):
        if Path(name).parent in touched:
            groups[Path(name).parent, is_test_source(Path(name))].append(name)
    packages = [record(package.as_posix(), module, count, limits.max_package_files,
                       limits, tests=tests)
                for (package, tests), members in sorted(groups.items())
                for module, limits in config.size_policies(members)
                for count in [sum(not path_ignored(p, config.get(module)) for p in members) if module else len(members)]]
    return {"files": files, "packages": packages}
