"""按加载角色检查文档体积。

角色由仓库相对路径决定；行数为物理行，PRP、JOTS 与 HTML 不限行数。AGENTS.md 只计 MDF 托管区块。
"""

from pathlib import Path
from typing import Iterable

from mdf_core.foundation.constants import (
    ADR_ROOT,
    ENTRY_DOCUMENTS,
    FACT_ROOTS,
    MDF_BLOCK_END,
    MDF_BLOCK_START,
    SIZE_ADR,
    SIZE_FACT,
    SIZE_PROJECT,
    SIZE_README,
    SIZE_ROUTER,
    SIZE_WORK_ITEM,
)
from mdf_core.foundation.errors import Finding
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.inspection.prose import structure_issues

ROUTER_PATHS = {
    "AGENTS.md",
    "docs/README.md",
    "docs/user-guide/README.md",
    "docs/system/overview.md",
}
WORK_ITEM_ROOTS = ("docs/proposals/", "docs/bugs/")


def size_role(rel: str) -> tuple[str, int] | None:
    if rel == "README.md":
        return SIZE_README
    if rel in ROUTER_PATHS:
        return SIZE_ROUTER
    if rel == "PROJECT.md":
        return SIZE_PROJECT
    parts = rel.split("/")
    if rel.startswith("docs/system/") and len(parts) == 4 and parts[3] == "index.md":
        return SIZE_ROUTER
    if any(rel.startswith(f"{root}/") for root in FACT_ROOTS):
        return SIZE_FACT
    if rel.startswith(f"{ADR_ROOT}/"):
        return SIZE_ADR
    if rel.startswith(WORK_ITEM_ROOTS) or rel == "docs/JOTS.md":
        return SIZE_WORK_ITEM
    return None


def role_text(path: Path, rel: str) -> str:
    """该文档受 MDF 约束的文本；AGENTS.md 只取托管区块。"""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        from mdf_core.documents.html_documents import visible_text
        text = visible_text(text)
    if rel == "AGENTS.md":
        start = text.find(MDF_BLOCK_START)
        end = text.find(MDF_BLOCK_END)
        if start < 0 or end < start:
            return ""
        text = text[start : end + len(MDF_BLOCK_END)]
    return text


def line_count(path: Path, rel: str) -> int:
    return len(role_text(path, rel).splitlines())


def sizable_documents(repo: Path) -> list[Path]:
    """全量检查面：根入口文档与 docs/ 下所有带角色的 Markdown。"""
    found: set[Path] = set()
    for raw in ENTRY_DOCUMENTS:
        path = repo / raw
        if path.is_file() and not path.is_symlink():
            found.add(path)
    docs = repo / "docs"
    if docs.is_dir() and not docs.is_symlink():
        found.update(
            path
            for path in docs.rglob("*")
            if path.is_file()
            and (path.suffix == ".md" or (path.suffix == ".html"
                 and path.relative_to(docs).parts[0] == "proposals"))
            and not path.name.endswith(".review.html")
            and not path.is_symlink()
            and path_stays_in_repo(repo, path)
        )
    return sorted(
        path for path in found if size_role(relative(repo, path)) is not None
    )


def size_findings(repo: Path, paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        rel = relative(repo, path)
        role = size_role(rel)
        if (path.suffix == ".html" or rel.startswith("docs/proposals/")
                or rel == "docs/JOTS.md" or role is None or not path.is_file()):
            continue
        name, limit = role
        count = line_count(path, rel)
        if count > limit:
            findings.append(
                Finding(
                    "size.hard",
                    f"{name} 文档 {count} 行，超过限制 {limit}；须按主题拆页或下沉，"
                    f"每个结果最多 {limit * 7 // 10} 行",
                    rel,
                )
            )
    return findings


def structure_findings(repo: Path, paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        rel = relative(repo, path)
        if size_role(rel) is None or rel == "docs/JOTS.md" or not path.is_file():
            continue
        for number, code, message in structure_issues(role_text(path, rel)):
            findings.append(Finding(code, f"第 {number} 行：{message}", rel))
    return findings


def command_prose_check(args) -> None:
    """列出结构硬限制违例：默认检查全部带角色文档，--path 指定任意仓库内 Markdown。"""
    from mdf_core.foundation.errors import MDFError, emit
    from mdf_core.workspace.gitutil import repo_path, require_git_root
    from mdf_core.execution.modules import MODULES_PATH, load_modules

    repo = repo_path(args.repo)
    require_git_root(repo)
    if args.path:
        paths = []
        for raw in args.path:
            path = (repo / raw).resolve()
            if (Path(raw).is_absolute() or not path_stays_in_repo(repo, path)
                    or not path.is_file() or path.suffix not in {".md", ".html"}):
                raise MDFError(f"--path 必须是仓库内的 Markdown 文件: {raw}", code="invalid_path")
            paths.append(path)
    else:
        paths = [path for path in sizable_documents(repo)
                 if relative(repo, path) != "docs/JOTS.md"]
    config = load_modules(repo) if (repo / MODULES_PATH).exists() else None
    ignored = sorted({relative(repo, path) for path in paths
                      if config and config.is_ignored(relative(repo, path))})
    paths = [path for path in paths if relative(repo, path) not in ignored]
    issues = [
        {"path": relative(repo, path), "line": number, "code": code, "message": message}
        for path in sorted(set(paths))
        for number, code, message in structure_issues(role_text(path, relative(repo, path)))
    ]
    emit({"ok": not issues, "operation": "prose-check", "checked": len(set(paths)),
          "issue_count": len(issues), "issues": issues, "ignored": ignored})
    if issues:
        raise SystemExit(2)
