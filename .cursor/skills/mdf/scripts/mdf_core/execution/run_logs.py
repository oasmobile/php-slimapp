"""每次 CLI 调用的运行日志，以及 .mdf/logs、.mdf/reports 的过期清理。"""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit

RETENTION_DAYS = 7
LOGS = ".mdf/logs"
REPORTS = ".mdf/reports"
FALLBACK_ENV = "MDF_LOG_DIR"


# CSI / OSC / 单字节 ESC 序列；落盘时去掉，终端原文保留。
_ANSI_RE = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07\x1B]*(?:\x07|\x1B\\))"
)


def stamp():
    return time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + f"{time.time_ns() % 10**9:09d}Z"


def strip_control(text: str) -> str:
    """去掉终端控制符，并把回车覆盖拆成多行，避免进度条污染日志。"""
    cleaned = _ANSI_RE.sub("", text)
    return cleaned.replace("\r\n", "\n").replace("\r", "\n")


def safe_name(value: str) -> str:
    name = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return name or "run"


def unique_dir(root, name):
    """在 root 下新建 <时间戳>-<name>；并发进程同名时追加序号。"""
    base = f"{stamp()}-{name}"
    for index in range(1, 1000):
        path = Path(root) / (base if index == 1 else f"{base}-{index}")
        try:
            path.mkdir()
            return path
        except FileExistsError:
            continue
    raise FileExistsError(base)


def ignored_dir(path):
    """建目录并在其中放 `*` 的 .gitignore，使内容不进 Git、不影响 clean 与指纹。"""
    path = Path(path)
    ignore = path / ".gitignore"
    if path.parent.is_symlink() or ignore.is_symlink():
        raise MDFError(f"日志与报告的父目录及 .gitignore 不允许 symbolic link: {path}", code="managed_symlink")
    path.mkdir(parents=True, exist_ok=True)
    if not ignore.is_file():
        ignore.write_text("*\n")
    return path


def prune(root, days=RETENTION_DAYS):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        return
    limit = time.time() - days * 86400
    for entry in root.iterdir():
        if entry.name == ".gitignore":
            continue
        try:
            if entry.lstat().st_mtime >= limit:
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        except OSError:
            continue


def _repo_hint(argv):
    for index, value in enumerate(argv):
        if value == "--repo" and index + 1 < len(argv):
            return argv[index + 1]
        if value.startswith("--repo="):
            return value.split("=", 1)[1]
    return None


def _main_repo(repo):
    try:
        common = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return repo
    return Path(common).parent


def _log_root(argv):
    """日志放主仓库的 .mdf/logs，交付 worktree 被 finish 删除后仍在；未接入 MDF 的目录用用户级目录。"""
    standalone = bool(argv and argv[0] in {"review-context", "fact-audit"} and any(
        token.split("=", 1)[0] == "--against" for token in argv))
    hint = None if standalone else _repo_hint(argv)
    if hint and Path(hint).is_dir():
        repo = Path(hint).resolve()
        main = _main_repo(repo)
        metadata = repo / ".mdf"
        if metadata.is_dir() and not metadata.is_symlink():
            prune(repo / REPORTS)
        main_metadata = main / ".mdf"
        logs = main / LOGS
        if main_metadata.is_dir() and not main_metadata.is_symlink():
            prune(logs)
            return ignored_dir(logs)
    fallback = os.environ.get(FALLBACK_ENV) or str(Path.home() / ".mdf" / "logs")
    prune(fallback)
    return ignored_dir(fallback)


def _argv_name(argv):
    if argv and argv[0] == "run":
        for index, value in enumerate(argv):
            if value == "--name" and index + 1 < len(argv):
                return safe_name(argv[index + 1])
            if value.startswith("--name="):
                return safe_name(value.split("=", 1)[1])
        return "run"
    return safe_name(argv[0] if argv else "none")


def _rel_log(path, repo):
    try:
        return str(Path(path).resolve().relative_to(repo))
    except ValueError:
        return str(Path(path).resolve())


def _pump(pipe, dest) -> None:
    if pipe is None:
        return
    try:
        fd = pipe.fileno()
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            dest.write(chunk.decode("utf-8", errors="replace"))
            dest.flush()
    except OSError:
        return


def stream_child(argv, *, cwd, env=None) -> int:
    """子进程原文写到 stderr（供终端与 RunLog）；不占用 stdout。"""
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    threads = [
        threading.Thread(target=_pump, args=(proc.stdout, sys.stderr), daemon=True),
        threading.Thread(target=_pump, args=(proc.stderr, sys.stderr), daemon=True),
    ]
    try:
        for thread in threads:
            thread.start()
        proc.wait()
        for thread in threads:
            thread.join()
    finally:
        for pipe in (proc.stdout, proc.stderr):
            if pipe is not None:
                pipe.close()
    return proc.returncode if proc.returncode is not None else 1


def command_run(args):
    """代跑任意命令：设 MDF_REPORT_DIR / NO_COLOR，由 RunLog 落盘，代替 Agent tee。"""
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise MDFError(f"run 的 --repo 不是目录: {repo}", code="invalid_arguments")
    cmd = list(args.command)
    if cmd[:1] == ["--"]:
        cmd = cmd[1:]
    if not cmd:
        raise MDFError("run 需要 `--` 后的命令", code="invalid_arguments")
    env = {**os.environ, "MDF_REPORT_DIR": str(args.log_path), "NO_COLOR": "1"}
    code = stream_child(cmd, cwd=repo, env=env)
    payload = {
        "exit_code": code,
        "log": _rel_log(args.log_path, repo),
        "command": cmd,
    }
    if code != 0:
        raise MDFError(f"run 命令失败: {cmd[0]}", code="run_failed", details=payload)
    emit({"ok": True, **payload})


class _Tee:
    def __init__(self, stream, sink):
        self._stream = stream
        self._sink = sink

    def write(self, text):
        self._sink.write(strip_control(text))
        return self._stream.write(text)

    def flush(self):
        self._sink.flush()
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


class RunLog:
    """把一次 CLI 调用的完整 stdout、stderr 与退出信息写入 <日志根>/<时间戳>-<命令>/。"""

    def __init__(self, argv):
        self.path = unique_dir(_log_root(argv), _argv_name(argv))
        self.argv = list(argv)
        self.started = time.time()

    def __enter__(self):
        self._files = [open(self.path / name, "w", encoding="utf-8")
                       for name in ("stdout.log", "stderr.log")]
        self._saved = sys.stdout, sys.stderr
        sys.stdout = _Tee(sys.stdout, self._files[0])
        sys.stderr = _Tee(sys.stderr, self._files[1])
        return self

    def finish(self, code):
        meta = {"argv": self.argv, "cwd": os.getcwd(), "exit_code": code,
                "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.started)),
                "seconds": round(time.time() - self.started, 3)}
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    def __exit__(self, *exc):
        sys.stdout, sys.stderr = self._saved
        for handle in self._files:
            handle.close()
        return False
