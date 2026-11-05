"""可选 HTTP 监听：把一条请求落成 inbox 文件。"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from mdf_core.foundation.errors import MDFError
from mdf_core.integrations.integrate_store import BUG_FIELDS, KINDS, now_stamp, read_yaml, write_message

MAX_BODY = 262144
_ID_RE = re.compile(r"^[0-9]{13}-[0-9a-f]{8}$")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("", "/"):
            self._json(404, {"ok": False, "error": "not_found"})
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > MAX_BODY:
            self._json(400, {"ok": False, "error": "bad_message"})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            message = incoming_message(payload)
        except (MDFError, UnicodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "bad_message"})
            return
        root: Path = self.server.repo_root  # type: ignore[attr-defined]
        session = read_yaml(root / "session.yaml")
        if message["kind"] != "ping" and payload.get("auth") != session.get("token"):
            self._json(401, {"ok": False, "error": "auth_rejected"})
            return
        try:
            write_message(root / "inbox", message)
        except MDFError:
            self._json(409, {"ok": False, "error": "duplicate_id"})
            return
        self._json(200, {"ok": True, "id": message["id"]})

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def incoming_message(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MDFError("消息必须是对象", code="bad_message")
    kind = payload.get("kind")
    identity = payload.get("from")
    message_id = payload.get("id")
    if kind not in KINDS or not isinstance(identity, dict):
        raise MDFError("消息缺少种类或来源", code="bad_message")
    if not isinstance(message_id, str) or not _ID_RE.fullmatch(message_id):
        raise MDFError("消息 id 不合法", code="bad_message")
    for key in ("repo", "branch", "commit"):
        if not isinstance(identity.get(key), str) or not identity[key]:
            raise MDFError("来源不完整", code="bad_message")
    body = payload.get("body")
    if kind == "bug-request":
        if not isinstance(body, dict) or any(
            not isinstance(body.get(key), str) or not str(body[key]).strip()
            for key in BUG_FIELDS
        ):
            raise MDFError("bug-request 字段不完整", code="bad_message")
        body = {key: body[key] for key in BUG_FIELDS}
    elif not isinstance(body, str):
        raise MDFError("正文必须是字符串", code="bad_message")
    elif kind == "send" and not body.strip():
        raise MDFError("send 需要正文", code="bad_message")
    reply_to = payload.get("reply_to") or ""
    if kind == "ack" and not str(reply_to).strip():
        raise MDFError("ack 需要 reply_to", code="bad_message")
    token = payload.get("token") or ""
    dest = payload.get("to") or ""
    at = payload.get("at") or ""
    if not isinstance(reply_to, str) or not isinstance(token, str):
        raise MDFError("reply_to 或 token 不合法", code="bad_message")
    if not isinstance(dest, str) or not isinstance(at, str):
        raise MDFError("to 或 at 不合法", code="bad_message")
    listen = identity.get("listen") or ""
    if not isinstance(listen, str):
        raise MDFError("listen 不合法", code="bad_message")
    return {
        "id": message_id,
        "kind": kind,
        "to": dest,
        "at": at or now_stamp(),
        "reply_to": reply_to,
        "token": token,
        "from": {
            "repo": identity["repo"],
            "branch": identity["branch"],
            "commit": identity["commit"],
            "listen": listen,
        },
        "body": body,
    }
