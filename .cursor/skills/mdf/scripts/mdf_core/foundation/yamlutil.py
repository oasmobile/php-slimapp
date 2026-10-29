import json
import re
from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError


def strip_inline_comment(value: str) -> str:
    """Remove a `` # comment`` suffix, ignoring ``#`` inside quotes."""
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char == "#" and index > 0 and value[index - 1] in (" ", "\t"):
            return value[:index].rstrip()
    return value


def unescape_double_quoted(value: str) -> str:
    """按 JSON 转义解码，与 yaml_quote 对称；含非法转义的手写值退回只还原反斜杠与引号。"""
    try:
        return json.loads(f'"{value}"')
    except ValueError:
        return (
            value.replace("\\\\", "\x00").replace('\\"', '"').replace("\x00", "\\")
        )


def split_flow_items(inside: str) -> list[str]:
    """Split a flow list body on commas that appear outside quotes."""
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for char in inside:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
            continue
        if char == ",":
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def scalar(value: str) -> Any:
    value = strip_inline_comment(value.strip())
    if not value:
        return {}
    if value in ("null", "Null", "NULL", "~"):
        return None
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False
    if value == "{}":
        return {}
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        if value[0] == '"':
            return unescape_double_quoted(value[1:-1])
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        if not inside:
            return []
        return [scalar(part.strip()) for part in split_flow_items(inside)]
    return value


def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by MDF without third-party packages."""
    raw_lines: list[tuple[int, str]] = []
    for number, original in enumerate(text.splitlines(), start=1):
        if "\t" in original[: len(original) - len(original.lstrip())]:
            raise MDFError(
                f"Tabs are not supported in YAML indentation (line {number})",
                code="invalid_yaml",
            )
        stripped = original.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(original) - len(original.lstrip(" "))
        raw_lines.append((indent, stripped))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, (indent, content) in enumerate(raw_lines):
        if content.startswith("- "):
            # A dash may share the indent of its list parent; only pop deeper
            # entries and sibling item mappings at the same indent.
            while stack and (
                indent < stack[-1][0]
                or (indent == stack[-1][0] and isinstance(stack[-1][1], dict))
            ):
                stack.pop()
        else:
            while stack and indent <= stack[-1][0]:
                stack.pop()
        if not stack:
            raise MDFError("Invalid YAML indentation", code="invalid_yaml")
        parent = stack[-1][1]

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise MDFError(
                    f"List item has no list parent: {content}",
                    code="invalid_yaml",
                )
            item_text = content[2:].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", item_text):
                key, value = item_text.split(":", 1)
                item: dict[str, Any] = {key.strip(): scalar(value)}
                parent.append(item)
                stack.append((indent, item))
            else:
                parent.append(scalar(item_text))
            continue

        if ":" not in content or not isinstance(parent, dict):
            raise MDFError(
                f"Invalid YAML entry: {content}", code="invalid_yaml"
            )
        key, value = content.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = scalar(value)
            continue

        next_is_list = (
            index + 1 < len(raw_lines)
            and raw_lines[index + 1][0] >= indent
            and raw_lines[index + 1][1].startswith("- ")
        )
        child: Any = [] if next_is_list else {}
        parent[key] = child
        stack.append((indent, child))
    return root


def parse_yaml(text: str) -> dict[str, Any]:
    # Deliberately always the subset parser: keeping an optional PyYAML path
    # made validation results depend on the local environment.
    return parse_yaml_subset(text)


def frontmatter_span(text: str) -> tuple[int, int, int]:
    """Locate the YAML frontmatter in raw document *text*.

    Returns ``(start, end, body_start)`` offsets: ``text[:start]`` is the
    opening ``---`` marker line, ``text[start:end]`` the frontmatter body, and
    ``text[body_start:]`` the document body. Both LF and CRLF line endings are
    accepted.
    """
    if text.lower().startswith("<!doctype html>"):
        from mdf_core.documents.html_documents import METADATA_OPEN, METADATA_CLOSE
        if text.count(METADATA_OPEN) != 1:
            raise MDFError("HTML 需要唯一 MDF metadata comment", code="missing_frontmatter")
        start = text.index(METADATA_OPEN) + len(METADATA_OPEN)
        end = text.find(METADATA_CLOSE, start)
        if end < 0:
            raise MDFError("HTML metadata comment 未结束", code="bad_frontmatter")
        return start, end, end + len(METADATA_CLOSE)
    if text.startswith("---\r\n"):
        start = 5
    elif text.startswith("---\n"):
        start = 4
    else:
        raise MDFError("Missing YAML frontmatter", code="missing_frontmatter")
    end_marker = re.search(r"\r?\n---(?:\r?\n|$)", text[start:])
    if end_marker is None:
        raise MDFError("Unterminated YAML frontmatter", code="bad_frontmatter")
    end = start + end_marker.start()
    return start, end, start + end_marker.end()


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    start, end, body_start = frontmatter_span(text)
    body = text[body_start:]
    if path.suffix == ".html":
        from mdf_core.documents.html_documents import visible_text
        body = visible_text(text)
    return parse_yaml(text[start:end]), body


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
