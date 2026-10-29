import re
from pathlib import Path

from mdf_core.foundation.constants import JOT_ID_RE
from mdf_core.foundation.errors import Finding, add_finding


ENTRY_RE = re.compile(
    r"<!-- jot: (?P<id>jot-[A-HJ-NP-Z0-9]{4}) -->\n"
    r"## (?P<title>[^\n]+)\n"
    r"(?P<body>.*?)"
    r"<!-- /jot -->\n?",
    re.DOTALL,
)


def validate_jots(repo: Path, findings: list[Finding]) -> None:
    path = repo / "docs/JOTS.md"
    relative = "docs/JOTS.md"
    if not path.exists() and not path.is_symlink():
        add_finding(findings, "jot.missing", "Missing docs/JOTS.md", relative)
        return
    if not path.is_file() or path.is_symlink():
        add_finding(
            findings,
            "jot.path",
            "docs/JOTS.md must be a regular repository file",
            relative,
        )
        return
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# 随手记录\n"):
        add_finding(
            findings,
            "jot.heading",
            "docs/JOTS.md 必须以“# 随手记录”开头",
            relative,
        )
        return
    _validate_entries(text[len("# 随手记录\n") :], findings, relative)


def _validate_entries(
    text: str,
    findings: list[Finding],
    relative: str,
) -> None:
    previous_end = 0
    identifiers: set[str] = set()
    for entry in ENTRY_RE.finditer(text):
        if text[previous_end : entry.start()].strip():
            add_finding(
                findings,
                "jot.format",
                "Jot content must be inside a marked entry",
                relative,
            )
            return
        identifier = entry.group("id")
        if not JOT_ID_RE.fullmatch(identifier):
            add_finding(
                findings,
                "jot.id",
                f"Invalid Jot ID: {identifier}",
                relative,
            )
        elif identifier in identifiers:
            add_finding(
                findings,
                "jot.id_duplicate",
                f"Duplicate Jot ID: {identifier}",
                relative,
            )
        identifiers.add(identifier)
        if not entry.group("body").strip():
            add_finding(
                findings,
                "jot.empty",
                f"Jot must have content: {identifier}",
                relative,
            )
        previous_end = entry.end()
    if text[previous_end:].strip():
        add_finding(
            findings,
            "jot.format",
            "Jot content must be inside a marked entry",
            relative,
        )
