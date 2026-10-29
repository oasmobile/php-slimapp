"""准备 CodeWiki 本地源码与缺失运行时；不改目标仓库或宿主设置。"""
import subprocess
import sys
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit

SOURCE = "https://github.com/FSoft-AI4Code/CodeWiki.git"


def run(args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise MDFError("CodeWiki 运行时命令失败", code="codewiki_runtime_failed",
                       details={"command": args, "exit_code": result.returncode,
                                "stderr": result.stderr[-2000:]})
    return result.stdout.strip()


def prepare(directory, source=SOURCE):
    directory = Path(directory).expanduser().absolute()
    if any(path.is_symlink() for path in (directory, *directory.parents)):
        raise MDFError("安装目录不得经过符号链接", code="unsafe_path")
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--", source, str(directory)], directory.parent)
    if not (directory / "pyproject.toml").is_file() or not (directory / "codewiki").is_dir():
        raise MDFError("CodeWiki 源码不完整", code="invalid_codewiki_source")
    if Path(run(["git", "rev-parse", "--show-toplevel"], directory)).resolve() != directory.resolve():
        raise MDFError("安装目录不是独立 Git 根", code="invalid_codewiki_source")
    if run(["git", "status", "--porcelain"], directory):
        raise MDFError("已有 CodeWiki 源码不干净", code="dirty_worktree")
    venv = directory / ".venv"
    python = venv / "bin/python"
    if not venv.exists():
        run([sys.executable, "-m", "venv", str(venv)], directory)
        run([str(python), "-m", "pip", "install", "-e", str(directory)], directory)
    if not python.is_file():
        raise MDFError("已有运行时不完整", code="invalid_codewiki_runtime")
    run([str(python), "-c", "from codewiki.mcp.server import server"], directory)
    return {"directory": str(directory), "python": str(python), "mcpServers": {
        "codewiki": {"command": str(python), "args": ["-m", "codewiki.mcp.server"], "cwd": str(directory)}}}


def command_codewiki_runtime(args):
    emit({"ok": True, "operation": "codewiki-runtime", "result": prepare(args.directory)})
