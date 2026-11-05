"""联调通道的本地文件。"""

from __future__ import annotations

import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.yamlutil import parse_yaml, yaml_quote

DIR_NAME = ".integration"
BUG_FIELDS = ("observed", "expected", "repro", "impact")
KINDS = ("ping", "courtesy", "ack", "heartbeat", "send", "bug-request", "end")


def new_id() -> str:
    return f"{int(time.time() * 1000):013d}-{secrets.token_hex(4)}"


def write_message(inbox: Path, message: dict[str, Any]) -> None:
    message_id = str(message["id"])
    target = inbox / f"{message_id}.yaml"
    if target.exists():
        raise MDFError("消息 id 已存在", code="duplicate_id")
    temporary = inbox / f".{message_id}.tmp"
    temporary.write_text(render_message(message), encoding="utf-8")
    temporary.replace(target)


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def party(identity: Any) -> str:
    if not isinstance(identity, dict):
        return "?"
    repo = str(identity.get("repo") or "")
    branch = str(identity.get("branch") or "")
    if repo and branch:
        return f"{repo}/{branch}"
    return repo or branch or "?"


def format_channel_entry(
    direction: str, message: dict[str, Any] | None = None
) -> str:
    at = str((message or {}).get("at") or now_stamp())
    if direction == "wait":
        return f"{at}  等待\n"
    label = "发出" if direction == "out" else "收到"
    source = party((message or {}).get("from"))
    dest = str((message or {}).get("to") or "本侧")
    kind = str((message or {}).get("kind") or "")
    message_id = str((message or {}).get("id") or "")
    reply_to = str((message or {}).get("reply_to") or "-")
    header = f"{at}  {label}  {source} -> {dest}  {kind}  id={message_id} reply_to={reply_to}\n"
    body = (message or {}).get("body")
    if isinstance(body, dict):
        text = "\n".join(
            f"{key}: {body[key]}" for key in BUG_FIELDS if key in body
        )
    else:
        text = str(body or "")
    if text:
        return f"{header}{text}\n\n"
    return f"{header}\n\n"


def render_message(message: dict[str, Any]) -> str:
    identity = message["from"]
    lines = [
        f"id: {yaml_quote(message['id'])}",
        f"kind: {yaml_quote(message['kind'])}",
        f"to: {yaml_quote(str(message.get('to') or ''))}",
        f"at: {yaml_quote(str(message.get('at') or ''))}",
        f"reply_to: {yaml_quote(message['reply_to'])}",
        f"token: {yaml_quote(message['token'])}",
        "from:",
        f"  repo: {yaml_quote(identity['repo'])}",
        f"  branch: {yaml_quote(identity['branch'])}",
        f"  commit: {yaml_quote(identity['commit'])}",
        f"  listen: {yaml_quote(identity['listen'])}",
    ]
    body = message["body"]
    if isinstance(body, dict):
        lines.append("body:")
        for key in BUG_FIELDS:
            lines.append(f"  {key}: {yaml_quote(body[key])}")
    else:
        lines.append(f"body: {yaml_quote(body)}")
    return "\n".join(lines) + "\n"


def next_pending(root: Path) -> dict[str, Any] | None:
    seen = read_seen(root)
    inbox = root / "inbox"
    for path in sorted(inbox.glob("*.yaml")):
        message = read_yaml(path)
        if str(message.get("id") or "") not in seen:
            return message
    return None


def pending_count(root: Path) -> int:
    seen = read_seen(root)
    return sum(
        1
        for path in (root / "inbox").glob("*.yaml")
        if str(read_yaml(path).get("id") or "") not in seen
    )


def read_seen(root: Path) -> set[str]:
    path = root / "seen"
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return {line.strip() for line in text.splitlines() if line.strip()}


def mark_seen(root: Path, message_id: str) -> None:
    with (root / "seen").open("a", encoding="utf-8") as handle:
        handle.write(message_id + "\n")


def read_peers(root: Path) -> dict[str, Any]:
    path = root / "peers.yaml"
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        return {}
    data = read_yaml(path)
    return data if isinstance(data, dict) else {}


def write_peers(root: Path, peers: dict[str, Any]) -> None:
    lines: list[str] = []
    for name in sorted(peers):
        record = peers[name]
        lines.append(f"{name}:")
        lines.append(f"  transport: {yaml_quote(str(record['transport']))}")
        if record["transport"] == "path":
            lines.append(f"  path: {yaml_quote(str(record['path']))}")
        else:
            lines.append(f"  url: {yaml_quote(str(record['url']))}")
        lines.append(f"  token: {yaml_quote(str(record.get('token') or ''))}")
    text = "\n".join(lines) + ("\n" if lines else "")
    (root / "peers.yaml").write_text(text, encoding="utf-8")


def write_session(repo: Path, token: str, listen: str) -> None:
    text = f"token: {yaml_quote(token)}\nlisten: {yaml_quote(listen)}\n"
    (repo / DIR_NAME / "session.yaml").write_text(text, encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    data = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MDFError(f"无法读取 {path.name}", code="invalid_yaml")
    return data
