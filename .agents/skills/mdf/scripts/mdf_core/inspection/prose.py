"""文档结构的硬限制：散文段、句子、列表项、节内散文与 emoji。"""
import re
import unicodedata

PROSE_BLOCK_LINES = 6
SENTENCE_WIDTH = 200
LIST_ITEM_LINES = 4
SECTION_PROSE_LINES = 15
ALLOWED_EMOJI = ("⚠️", "✅", "❌", "💡", "📌", "📂", "📍", "⬇️")
_ALLOWED_BASES = {emoji.rstrip("\uFE0F") for emoji in ALLOWED_EMOJI}

_HEADING = re.compile(r"#{1,6}\s")
_ITEM = re.compile(r"(\s*)(?:[-*+]|\d+[.)])\s+")
_FENCE = re.compile(r"\s*(```|~~~)")
_LINK = re.compile(r"\]\([^)]*\)")
_SENTENCE_END = re.compile(r"(?<=[。；！？])|(?<=[.;!?])\s+")
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]\uFE0F?")


def width(text):
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def _join(lines):
    text = ""
    for line in lines:
        if text and (text[-1].isascii() or line[:1].isascii()):
            text += " "
        text += line
    return _LINK.sub("]", text)


def _long_sentences(lines, number, issues):
    for sentence in _SENTENCE_END.split(_join(lines)):
        sentence = sentence.strip()
        if width(sentence) > SENTENCE_WIDTH:
            issues.append((number, "prose.sentence",
                           f"单句显示宽度 {width(sentence)}，超过 {SENTENCE_WIDTH}；拆句后每句显示宽度最多 140"))


def _body(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return [(number, "") for number in range(1, index + 2)] + [
                    (index + 2 + offset, line) for offset, line in enumerate(lines[index + 1:])
                ]
    return list(enumerate(lines, 1))


def structure_issues(text):
    """返回 (行号, code, 说明) 列表；检查当前硬限制；超限后的拆分结果由审阅复核。"""
    issues = []
    block, item, item_indent, section_prose, section_start = [], [], -1, 0, 1
    fenced = False

    def close_block():
        nonlocal block
        if len(block) > PROSE_BLOCK_LINES:
            issues.append((block[0][0], "prose.block",
                           f"连续散文 {len(block)} 行，超过 {PROSE_BLOCK_LINES}；拆分后每段最多 4 行"))
        if block:
            _long_sentences([line for _, line in block], block[0][0], issues)
        block = []

    def close_item():
        nonlocal item, item_indent
        if len(item) > LIST_ITEM_LINES:
            issues.append((item[0][0], "prose.list_item",
                           f"列表项 {len(item)} 行，超过 {LIST_ITEM_LINES}；拆分后每项最多 2 行"))
        if item:
            _long_sentences([line for _, line in item], item[0][0], issues)
        item, item_indent = [], -1

    def close_section(number):
        nonlocal section_prose, section_start
        if section_prose > SECTION_PROSE_LINES:
            issues.append((section_start, "prose.section",
                           f"本节散文共 {section_prose} 行，超过 {SECTION_PROSE_LINES}；拆分后每节散文最多 10 行"))
        section_prose, section_start = 0, number

    for number, raw in _body(text):
        for match in _EMOJI.finditer(raw):
            if match.group(0).rstrip("\uFE0F") not in _ALLOWED_BASES:
                issues.append((number, "prose.emoji",
                               f"emoji {match.group(0)} 不在允许集合 {' '.join(ALLOWED_EMOJI)} 内"))
        if _FENCE.match(raw):
            close_block()
            close_item()
            fenced = not fenced
            continue
        stripped = raw.strip()
        if fenced:
            continue
        if not stripped:
            close_block()
            close_item()
            continue
        if _HEADING.match(raw):
            close_block()
            close_item()
            close_section(number)
            continue
        marker = _ITEM.match(raw)
        if marker:
            close_block()
            close_item()
            item, item_indent = [(number, raw[marker.end():].strip())], len(marker.group(1))
            continue
        indent = len(raw) - len(raw.lstrip())
        if item and indent > item_indent:
            item.append((number, stripped))
            continue
        close_item()
        if stripped.startswith(("|", "<")):
            close_block()
            continue
        block.append((number, stripped.lstrip("> ").strip()))
        section_prose += 1
    close_block()
    close_item()
    close_section(0)
    return issues
