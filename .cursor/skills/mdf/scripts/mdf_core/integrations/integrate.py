"""本机 inbox 与可选 HTTP 的联调通道。"""

from __future__ import annotations

import json
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.integrations.integrate_http import Handler
from mdf_core.integrations.integrate_store import (
    BUG_FIELDS,
    DIR_NAME,
    KINDS,
    format_channel_entry,
    mark_seen,
    new_id,
    next_pending,
    now_stamp,
    pending_count,
    read_peers,
    read_yaml,
    write_message,
    write_peers,
    write_session,
)
from mdf_core.workspace.gitutil import (
    current_branch,
    primary_worktree,
    repo_path,
    require_git_root,
    run,
    worktree_map,
)

IGNORE_LINE = ".integration/"
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")


def command_integrate(args: Any) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    action = args.action
    if action == "init":
        emit(_init(repo))
    elif action == "peer":
        emit(_peer(repo, args))
    elif action == "send":
        print(format_channel_entry("out", _send(repo, args)), end="", flush=True)
    elif action == "poll":
        try:
            wait = _WAIT_LOG if args.wait is None else args.wait
            _poll(repo, args.timeout, wait)
        except KeyboardInterrupt:
            return
    elif action == "listen":
        _listen(repo, args.bind)
    elif action == "status":
        emit(_status(repo))
    else:
        raise MDFError(f"未知 integrate 动作：{action}", code="bad_action")


def _root(repo: Path) -> Path:
    path = repo / DIR_NAME
    if not (path / "session.yaml").is_file():
        raise MDFError("尚未 integrate init", code="channel_missing")
    return path


def _init(repo: Path) -> dict[str, Any]:
    root = repo / DIR_NAME
    inbox = root / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    session_path = root / "session.yaml"
    if session_path.is_file():
        token = str(read_yaml(session_path).get("token") or "")
        listen = str(read_yaml(session_path).get("listen") or "")
    else:
        token = secrets.token_hex(18)
        listen = ""
    if not token:
        token = secrets.token_hex(18)
    write_session(repo, token, listen)
    _ensure_gitignore(repo)
    (root / "peers.yaml").touch(exist_ok=True)
    return {"ok": True, "token": token, "gitignore": IGNORE_LINE}


def _ensure_gitignore(repo: Path) -> None:
    path = repo / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = text.splitlines()
    if any(line.strip() == IGNORE_LINE for line in lines):
        return
    suffix = "" if text.endswith("\n") or not text else "\n"
    path.write_text(f"{text}{suffix}{IGNORE_LINE}\n", encoding="utf-8")


def _peer(repo: Path, args: Any) -> dict[str, Any]:
    root = _root(repo)
    name = args.name or ""
    if not args.target:
        raise MDFError("peer 需要 --name 与 --target", code="bad_peer")
    if not _NAME_RE.fullmatch(name):
        raise MDFError("peer 名称不合法", code="bad_peer")
    peers = read_peers(root)
    previous = peers.get(name, {})
    record = _classify(repo, args.target)
    if args.token is not None:
        record["token"] = args.token
    elif isinstance(previous, dict) and previous.get("token"):
        record["token"] = str(previous["token"])
    else:
        record["token"] = ""
    peers[name] = record
    write_peers(root, peers)
    return {"ok": True, "name": name, "peer": record}


def _classify(repo: Path, target: str) -> dict[str, str]:
    if target.startswith("http://"):
        return {"transport": "http", "url": _http_url(target)}
    path = Path(target)
    if path.is_absolute():
        resolved = path.resolve()
        if not resolved.is_dir():
            raise MDFError("对端路径不是目录", code="bad_peer")
        return {"transport": "path", "path": str(resolved)}
    trees = worktree_map(repo)
    found = trees.get(target)
    if found is None:
        raise MDFError("对端不是绝对路径、http URL 或本仓 worktree", code="bad_peer")
    return {"transport": "path", "path": str(found.resolve())}


def _http_url(target: str) -> str:
    parsed = urlparse(target)
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise MDFError("http 对端必须是 http://host:port", code="bad_peer")
    return f"http://{parsed.hostname}:{parsed.port}/"


def _send(repo: Path, args: Any) -> dict[str, Any]:
    root = _root(repo)
    kind = args.kind or "send"
    if kind not in KINDS:
        raise MDFError("kind 不合法", code="bad_message")
    if not args.to:
        raise MDFError("send 需要 --to", code="peer_unknown")
    peers = read_peers(root)
    peer = peers.get(args.to)
    if not isinstance(peer, dict):
        raise MDFError("未知 peer", code="peer_unknown")
    message = _message(repo, kind, args)
    _deliver(peer, message)
    return message


def _compose(
    repo: Path, kind: str, dest: str, reply_to: str = "", body: Any = ""
) -> dict[str, Any]:
    session = read_yaml(repo / DIR_NAME / "session.yaml")
    return {
        "id": new_id(),
        "kind": kind,
        "to": dest,
        "at": now_stamp(),
        "reply_to": reply_to,
        "token": str(session.get("token") or ""),
        "from": _identity(repo, str(session.get("listen") or "")),
        "body": body,
    }


def _message(repo: Path, kind: str, args: Any) -> dict[str, Any]:
    return _compose(
        repo, kind, args.to or "", args.reply_to or "", _body(kind, args)
    )


def _deliver(peer: dict[str, Any], message: dict[str, Any]) -> None:
    transport = str(peer.get("transport") or "")
    if transport == "path":
        _deliver_path(peer, message)
    elif transport == "http":
        _deliver_http(peer, message)
    else:
        raise MDFError("peer 传输方式不合法", code="bad_peer")


def _body(kind: str, args: Any) -> Any:
    fields = {
        "observed": args.observed,
        "expected": args.expected,
        "repro": args.repro,
        "impact": args.impact,
    }
    supplied = [key for key, value in fields.items() if value is not None]
    if kind == "bug-request":
        if supplied != list(BUG_FIELDS) or args.body is not None:
            raise MDFError(
                "bug-request 需要 observed、expected、repro、impact",
                code="bad_message",
            )
        if any(not str(fields[key]).strip() for key in BUG_FIELDS):
            raise MDFError("bug-request 字段不能为空", code="bad_message")
        return {key: str(fields[key]) for key in BUG_FIELDS}
    if supplied:
        raise MDFError("只有 bug-request 接受缺陷字段", code="bad_message")
    text = args.body or ""
    if kind == "send" and not text.strip():
        raise MDFError("send 需要正文", code="bad_message")
    if kind == "ack" and not str(args.reply_to or "").strip():
        raise MDFError("ack 需要 --reply-to", code="bad_message")
    return text


def _identity(repo: Path, listen: str) -> dict[str, str]:
    commit = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    return {
        "repo": primary_worktree(repo).name,
        "branch": current_branch(repo),
        "commit": commit,
        "listen": listen,
    }


def _deliver_path(peer: dict[str, Any], message: dict[str, Any]) -> None:
    target = Path(str(peer.get("path") or ""))
    inbox = target / DIR_NAME / "inbox"
    if not inbox.is_dir():
        raise MDFError("对端尚未 integrate init", code="peer_not_ready")
    write_message(inbox, message)


def _deliver_http(peer: dict[str, Any], message: dict[str, Any]) -> None:
    url = str(peer.get("url") or "")
    payload = dict(message)
    payload["auth"] = str(peer.get("token") or "")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        try:
            if exc.code == 401:
                raise MDFError(
                    "对端拒绝了会话 token", code="auth_rejected"
                ) from exc
            detail = exc.read().decode("utf-8", errors="replace")
            raise MDFError(
                f"对端 HTTP {exc.code}", code="http_rejected", details=detail
            ) from exc
        finally:
            exc.close()
    except urllib.error.URLError as exc:
        raise MDFError(f"无法连接对端：{exc.reason}", code="peer_unreachable") from exc
    try:
        body = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise MDFError("对端响应不是 JSON", code="bad_response") from exc
    if not isinstance(body, dict) or not body.get("ok"):
        raise MDFError("对端未确认写入", code="bad_response")


_POLL_SLEEP = 0.05
_WAIT_LOG = 60.0


def _heartbeat_peers(repo: Path) -> None:
    peers = read_peers(_root(repo))
    for name, peer in peers.items():
        if not isinstance(peer, dict):
            continue
        message = _compose(repo, "heartbeat", name)
        try:
            _deliver(peer, message)
        except MDFError:
            continue
        print(format_channel_entry("out", message), end="", flush=True)


def _poll(repo: Path, timeout: float | None, wait: float = _WAIT_LOG) -> None:
    root = _root(repo)
    deadline = None if timeout is None else time.monotonic() + timeout
    last_wait = 0.0
    interval = _WAIT_LOG if wait <= 0 else wait
    while True:
        now = time.monotonic()
        if deadline is not None and now >= deadline:
            print(f"{now_stamp()}  超时\n", end="", flush=True)
            return
        message = next_pending(root)
        if message is not None:
            mark_seen(root, str(message["id"]))
            print(format_channel_entry("in", message), end="", flush=True)
            continue
        if last_wait == 0.0 or now - last_wait >= interval:
            print(format_channel_entry("wait"), end="", flush=True)
            if last_wait != 0.0:
                _heartbeat_peers(repo)
            last_wait = now
        time.sleep(_POLL_SLEEP)


def _listen(repo: Path, bind: str) -> None:
    root = _root(repo)
    host, port = _bind(bind)
    server = ThreadingHTTPServer((host, port), Handler)
    server.repo_root = root  # type: ignore[attr-defined]
    bound_host, bound_port = server.server_address[:2]
    url = f"http://{bound_host}:{bound_port}/"
    session = read_yaml(root / "session.yaml")
    write_session(repo, str(session.get("token") or ""), url)
    emit({"ok": True, "listen": url})
    sys.stdout.flush()
    try:
        server.serve_forever()
    finally:
        server.server_close()
        write_session(repo, str(session.get("token") or ""), "")


def _status(repo: Path) -> dict[str, Any]:
    root = _root(repo)
    session = read_yaml(root / "session.yaml")
    return {
        "ok": True,
        "token": session.get("token") or "",
        "listen": session.get("listen") or "",
        "pending": pending_count(root),
        "peers": read_peers(root),
    }


def _bind(value: str) -> tuple[str, int]:
    host, separator, port_text = value.rpartition(":")
    if not separator or not host:
        raise MDFError("bind 必须是 host:port", code="bad_bind")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise MDFError("端口不是整数", code="bad_bind") from exc
    if port < 0 or port > 65535:
        raise MDFError("端口超出范围", code="bad_bind")
    return host, port
