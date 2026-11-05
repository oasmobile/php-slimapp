"""HTML 工作材料：可见正文为唯一正文，YAML metadata 存在指定 comment 中。"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from mdf_core.foundation.errors import MDFError

METADATA_OPEN = "<!-- MDF:METADATA\n"
METADATA_CLOSE = "\n-->"


class DocumentParser(HTMLParser):
    """将 main 的可见正文投影为结构文本，供对象校验与 draft 修订使用。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.main_count = 0
        self.active = False
        self.hidden = 0
        self.links = []
        self.headings = []
        self.heading = None
        self.heading_id = None
        self.outline = []
        self.cells = 0
        self.pre = False
        self.suppressed = []
        self.list_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "main":
            self.main_count += 1
            self.active = True
        if not self.active:
            return
        if tag in {"script", "style", "template"} or "hidden" in values:
            self.hidden += 1
            self.suppressed.append(tag)
        if self.hidden:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
            self.heading = []
            self.heading_id = values.get("id") if tag == "h2" else None
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            if self.list_depth == 1:
                self.parts.append("\n")
        elif tag in {"p", "section", "pre"}:
            self.parts.append("\n\n")
        elif tag == "li":
            raw_indent = values.get("data-indent", "0")
            if not raw_indent.isdigit() or int(raw_indent) > 120:
                raise MDFError("HTML list 缩进必须为 0–120", code="invalid_html")
            indent = int(raw_indent)
            self.parts.append("\n" + " " * indent + values.get("data-marker", "-") + " ")
        elif tag == "a":
            self.parts.append("[")
            self.links.append(values.get("href", ""))
        elif tag == "img":
            self.parts.append(f"![{values.get('alt', '')}]({values.get('src', '')})")
        elif tag == "code":
            if not self.pre:
                self.parts.append("`")
        if tag == "pre":
            self.pre = True
            self.parts.append("```\n")
        if tag == "br":
            self.parts.append("\n")
        elif tag == "tr":
            self.parts.append("\n|")
            self.cells = 0
        elif tag in {"td", "th"}:
            self.cells += 1
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if not self.active:
            return
        if self.hidden:
            if self.suppressed and tag == self.suppressed[-1]:
                self.hidden -= 1
                self.suppressed.pop()
            return
        if re.fullmatch(r"h[1-6]", tag):
            heading = "".join(self.heading or []).strip()
            self.headings.append(heading)
            if self.heading_id:
                self.outline.append((self.heading_id, heading))
            self.heading = None
            self.heading_id = None
            self.parts.append("\n\n")
        elif tag == "a" and self.links:
            target = self.links.pop()
            self.parts.append("](" + (f"<{target}>" if " " in target else target) + ")")
        elif tag == "code":
            if not self.pre:
                self.parts.append("`")
        elif tag == "pre":
            self.pre = False
            self.parts.append("\n```\n\n")
        elif tag in {"td", "th"}:
            self.parts.append(" |")
        elif tag == "thead":
            self.parts.append("\n|" + " --- |" * self.cells)
        elif tag in {"ul", "ol"}:
            self.list_depth -= 1
            if self.list_depth == 0:
                self.parts.append("\n\n")
        elif tag in {"p", "table"}:
            self.parts.append("\n")
        elif tag == "main":
            self.active = False

    def handle_data(self, data):
        if self.active and not self.hidden:
            if self.list_depth and not self.pre and not data.strip():
                return
            if self.list_depth and not self.pre:
                data = re.sub(r"[\r\n]+\s*", " ", data)
            self.parts.append(data)
            if self.heading is not None:
                self.heading.append(data)


def visible_text(text):
    parser = DocumentParser()
    parser.feed(text)
    if parser.main_count != 1:
        raise MDFError("HTML 必须含唯一 main 正文", code="invalid_html")
    return re.sub(r"\n{3,}", "\n\n", "".join(parser.parts)).strip() + "\n"


def inline(text):
    """Escape first, then render the supported Markdown inline syntax."""
    tokens = re.compile(r"`[^`]+`|!?\[[^\]]*\]\((?:<[^>]+>|[^)]+)\)|\*\*[^*]+\*\*")
    result, cursor = [], 0
    for match in tokens.finditer(text):
        result.append(html.escape(text[cursor:match.start()]))
        token = match.group()
        if token.startswith("`"):
            result.append("<code>" + html.escape(token[1:-1]) + "</code>")
        elif token.startswith("**"):
            result.append("<strong>" + html.escape(token[2:-2]) + "</strong>")
        else:
            label, target = token[token.index("[") + 1:].split("](", 1)
            target = target[:-1]
            target = target[1:target.index(">")] if target.startswith("<") else target.split()[0]
            if token.startswith("!"):
                result.append(f'<img alt="{html.escape(label)}" src="{html.escape(target)}">')
            else:
                result.append(f'<a href="{html.escape(target)}">{inline(label)}</a>')
        cursor = match.end()
    return "".join(result) + html.escape(text[cursor:])


def markdown_body(body):
    """Render headings, paragraphs, lists, tables and fenced code without dependencies."""
    output, paragraph, lists = [], [], []
    lines = body.splitlines()
    index = 0

    def flush():
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()
        while lists:
            close_list()

    def close_list():
        _, tag = lists.pop()
        output.append(f"</li></{tag}>")

    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush()
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            output.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
        elif re.match(r"^#{1,6} ", line):
            flush()
            level, text = line.split(" ", 1)
            anchor = html.escape(text.strip().lower().replace(" ", "-"))
            output.append(f'<h{len(level)} id="{anchor}">{inline(text)}</h{len(level)}>')
        elif line.startswith("|") and index + 1 < len(lines) and re.match(
            r"^\|[ :|\-]+\|$", lines[index + 1]
        ):
            flush()
            cells = lambda row: [inline(cell.strip()) for cell in row.strip("|").split("|")]
            output.append('<div class="table-wrap"><table><thead><tr>'
                          + "".join(f"<th>{v}</th>" for v in cells(line)))
            output.append("</tr></thead><tbody>")
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                output.append("<tr>" + "".join(f"<td>{v}</td>" for v in cells(lines[index])) + "</tr>")
                index += 1
            output.append("</tbody></table></div>")
            continue
        elif match := re.match(r"^(\s*)([-*]|\d+\.) (.+)$", line):
            tag = "ol" if re.match(r"^\s*\d+\.", line) else "ul"
            indent = len(match.group(1))
            while lists and (indent < lists[-1][0] or (indent == lists[-1][0] and tag != lists[-1][1])):
                close_list()
            if lists and indent == lists[-1][0]:
                output.append("</li>")
            else:
                if paragraph:
                    output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
                    paragraph.clear()
                output.append(f"<{tag}>")
                lists.append((indent, tag))
            value = f' value="{int(match.group(2)[:-1])}"' if tag == "ol" else ""
            output.append(f'<li data-indent="{indent}" data-marker="{match.group(2)}"{value}>'
                          + inline(match.group(3)))
        elif not line.strip():
            flush()
        else:
            if lists:
                output.append(" " + inline(line.strip()))
            else:
                paragraph.append(line.strip())
        index += 1
    flush()
    return "\n".join(output)


def render_document(content, title, metadata=None):
    """给 PRP 与 HTML 总结正文套用同一份离线文档模板。"""
    template = Path(__file__).resolve().parents[3] / "assets/templates/document.html"
    parser = DocumentParser()
    parser.feed("<main>" + content + "</main>")
    outline = "\n".join(f'<li><a href="#{html.escape(anchor)}">{html.escape(label)}</a></li>'
                        for anchor, label in parser.outline)
    comment = ""
    if metadata is not None:
        fields = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
        fields = fields.replace("-->", r"\u002d\u002d\u003e")
        comment = METADATA_OPEN + fields + METADATA_CLOSE
    slots = {"{{MDF_METADATA_COMMENT}}": comment, "{{MDF_DOCUMENT_TITLE}}": html.escape(title),
             "{{MDF_DOCUMENT_OUTLINE}}": outline, "{{MDF_DOCUMENT_CONTENT}}": content}
    return re.sub(r"\{\{MDF_[A-Z_]+\}\}", lambda match: slots[match.group()], template.read_text())


def render_html(metadata, body):
    title = next((line[2:] for line in body.splitlines() if line.startswith("# ")), "MDF")
    return render_document(markdown_body(body), title, metadata)


def update_metadata(text, metadata):
    from mdf_core.foundation.yamlutil import frontmatter_span
    start, end, _ = frontmatter_span(text)
    fields = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    return text[:start] + fields.replace("-->", r"\u002d\u002d\u003e") + text[end:]
