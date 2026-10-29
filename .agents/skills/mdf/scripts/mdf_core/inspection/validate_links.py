from pathlib import Path
import html
import re
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import unquote

from mdf_core.foundation.constants import ALL_MARKDOWN_LINK_RE
from mdf_core.foundation.errors import Finding, MDFError, add_finding, serialize_findings
from mdf_core.foundation.paths import path_stays_in_repo, relative


EXTERNAL_LINK_PREFIXES = ("http://", "https://", "mailto:", "data:")
HTML_ATTRIBUTE_RE = re.compile(r'''\s+([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))''')


class HTMLLinks(HTMLParser):
    """只从真实 tag 的 href/src 取链接，保留原字符串中的精确位置。"""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.line_starts = [0, *[match.end() for match in re.finditer("\n", text)]]
        self.spans = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        row, column = self.getpos()
        offset = self.line_starts[row - 1] + column
        for match in HTML_ATTRIBUTE_RE.finditer(self.get_starttag_text()):
            if match.group(1).lower() not in {"href", "src"}:
                continue
            group = next(index for index in (2, 3, 4) if match.group(index) is not None)
            self.spans.append((offset + match.start(group), offset + match.end(group),
                               html.unescape(match.group(group))))


def document_link_spans(path: Path, text: str):
    """返回 href/src 或 Markdown link 的原始位置与解码 target。"""
    if path.suffix == ".html":
        return HTMLLinks(text).spans
    return [(match.start(1), match.end(1), match.group(1))
            for match in ALL_MARKDOWN_LINK_RE.finditer(text)]


def is_external_link(target: str) -> bool:
    return target.startswith(EXTERNAL_LINK_PREFIXES)


def resolve_local_link(source: Path, target: str) -> Path:
    """Resolve a Markdown href relative to the file that contains it.

    A leading `/` is site-root (filesystem-absolute), not the repository root.
    """
    return (source.parent / target).resolve()


def canonical_local_link(
    repo: Path,
    source: Path,
    target: str,
    delivery_root: Path | None = None,
) -> str | None:
    """Fingerprint form of a local href, or None to keep the original raw target.

    Missing files are never treated as inside the delivery directory.
    """
    if not target or is_external_link(target):
        return None
    absolute = resolve_local_link(source, target)
    if not path_stays_in_repo(repo, absolute):
        return None
    relative_path = absolute.relative_to(repo).as_posix()
    if (
        delivery_root is not None
        and absolute.exists()
        and (absolute == delivery_root or delivery_root in absolute.parents)
    ):
        return "@delivery/" + absolute.relative_to(delivery_root).as_posix()
    return relative_path


def managed_markdown(repo: Path) -> Iterable[Path]:
    roots = (
        repo / "PROJECT.md",
        repo / "GLOSSARY.md",
        repo / "CHANGELOG.md",
        repo / "changes",
        repo / "docs",
    )
    found: set[Path] = set()
    for root in roots:
        if root.is_symlink() or not path_stays_in_repo(repo, root):
            continue
        if root.is_file():
            found.add(root)
        elif root.is_dir():
            found.update(
                path
                for path in root.rglob("*")
                if path.is_file()
                and (path.suffix == ".md" or (path.suffix == ".html" and (
                    root.name == "docs" and path.relative_to(root).parts[0] == "proposals"
                    or root.name == "changes" and path.name == "delivery-summary.html")))
                and not path.name.endswith(".review.html")
                and not path.is_symlink()
                and path_stays_in_repo(repo, path)
            )
    return sorted(found)


def split_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        parts = target.split(maxsplit=1)
        target = parts[0] if parts else ""
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def document_link_target(path: Path, raw: str) -> str:
    return split_link_target(f"<{raw}>" if path.suffix == ".html" else raw)


def collect_local_link_findings(
    repo: Path, path: Path, findings: list[Finding]
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    for _, _, raw in document_link_spans(path, text):
        target = document_link_target(path, raw)
        if not target:
            if raw and not raw.strip():
                add_finding(
                    findings,
                    "link.broken",
                    f"Broken local link: {raw}",
                    relative(repo, path),
                )
            continue
        if is_external_link(target):
            continue
        resolved = resolve_local_link(path, target)
        if not path_stays_in_repo(repo, resolved):
            add_finding(
                findings,
                "link.outside_repo",
                f"Local link escapes the repository: {raw}",
                relative(repo, path),
            )
            continue
        if not resolved.exists():
            add_finding(
                findings,
                "link.broken",
                f"Broken local link: {raw}",
                relative(repo, path),
            )


def validate_links(repo: Path, findings: list[Finding]) -> None:
    for path in managed_markdown(repo):
        collect_local_link_findings(repo, path, findings)


def require_existing_local_links(repo: Path, paths: Iterable[Path]) -> None:
    findings: list[Finding] = []
    for path in paths:
        collect_local_link_findings(repo, path, findings)
    if findings:
        raise MDFError(
            "设计材料含无效本地链接",
            code="broken_link",
            details={"findings": serialize_findings(findings)},
        )
