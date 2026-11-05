"""overview.md 核心模块表的确定性检查。"""

from __future__ import annotations

import re
from pathlib import Path

from mdf_core.foundation.constants import CORE_MODULE_ROWS, OVERVIEW_RELATIVE
from mdf_core.foundation.errors import Finding

_LINK_CELL = re.compile(r"\[[^\]]*\]\([^)]+\)")
_TABLE_SEP = re.compile(r"^:?-+:?$")


def _pipe_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _core_module_cell_ok(cell: str) -> bool:
    text = cell.strip()
    if _LINK_CELL.search(text):
        return True
    for prefix in ("不适用：", "不适用:"):
        if text.startswith(prefix) and text[len(prefix):].strip():
            return True
    return False


def overview_core_module_findings(
    repo: Path, documents: list[Path]
) -> list[Finding]:
    overview = (repo / OVERVIEW_RELATIVE).resolve()
    if overview not in {path.resolve() for path in documents}:
        return []
    rel = OVERVIEW_RELATIVE
    if not overview.is_file() or overview.is_symlink():
        return [
            Finding("overview.core_modules", "overview.md 无法读取", rel)
        ]
    lines = overview.read_text(encoding="utf-8").splitlines()
    start = next(
        (
            index + 1
            for index, line in enumerate(lines)
            if re.match(r"^##\s+核心模块\s*$", line)
        ),
        None,
    )
    if start is None:
        return [
            Finding("overview.core_modules", "缺少「## 核心模块」", rel)
        ]
    body: list[str] = []
    for line in lines[start:]:
        if re.match(r"^#+\s+", line):
            break
        body.append(line)
    rows: list[tuple[str, str]] = []
    header_seen = False
    for line in body:
        cells = _pipe_cells(line)
        if cells is None or len(cells) < 2:
            if header_seen and rows:
                break
            continue
        if _TABLE_SEP.match(cells[0].replace(" ", "")):
            continue
        if not header_seen:
            header_seen = True
            continue
        rows.append((cells[0], cells[1]))
    if not header_seen:
        return [
            Finding("overview.core_modules", "核心模块表缺失", rel)
        ]
    names = [name for name, _ in rows]
    expected = list(CORE_MODULE_ROWS)
    if names != expected:
        joined = "、".join(expected)
        return [
            Finding(
                "overview.core_modules",
                f"核心模块表须为 {joined} 五行",
                rel,
            )
        ]
    findings: list[Finding] = []
    for name, cell in rows:
        if _core_module_cell_ok(cell):
            continue
        findings.append(
            Finding(
                "overview.core_modules",
                f"{name} 行须为主题叶链接或「不适用：」加理由",
                rel,
            )
        )
    return findings


_PROJECT_ENTRY_PATHS = (
    "docs/system/overview.md",
    "docs/README.md",
    "docs/system/testing/index.md",
)


def project_entry_link_findings(
    repo: Path, sized: list[Path]
) -> list[Finding]:
    path = repo / "PROJECT.md"
    if path.resolve() not in {item.resolve() for item in sized}:
        return []
    if not path.is_file() or path.is_symlink():
        return []
    text = path.read_text(encoding="utf-8")
    missing = [
        target for target in _PROJECT_ENTRY_PATHS if target not in text
    ]
    if not missing:
        return []
    joined = " 与 ".join(missing)
    return [
        Finding(
            "project.entry_links",
            f"PROJECT.md 须指向 {joined}",
            "PROJECT.md",
        )
    ]
