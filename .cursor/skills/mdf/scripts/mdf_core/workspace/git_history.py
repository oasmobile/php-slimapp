"""批量预取 HEAD 的有限线性 history；复杂 history 仍交给逐路径 git log。"""
import os
import re
import subprocess
from pathlib import Path, PurePosixPath


def recent_path_commits(repo: Path) -> dict[str, str]:
    """最多读取 64 个 commit，遇 merge 即停，不推断 path-specific merge simplification。"""
    result = subprocess.run(
        ["git", "log", "--first-parent", "--max-count=64", "--format=%x00%H%x00%P",
         "--name-only", "-z", "--no-renames", "--ignore-submodules=none", "--diff-merges=off", "--no-ext-diff",
         "--no-textconv", "--no-show-signature", "--no-decorate", "--no-color", "--"],
        cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        return {}
    fields = result.stdout.split(b"\0")
    commits: dict[str, str] = {}
    position = 0
    while position + 2 < len(fields):
        marker, commit, parents = fields[position:position + 3]
        if marker or not re.fullmatch(rb"[0-9a-f]{40,64}", commit):
            return {}
        if len(parents.split()) > 1:
            break
        sha = commit.decode("ascii")
        position += 3
        first = True
        while position < len(fields) and fields[position]:
            raw = fields[position]
            if first:
                raw = raw.removeprefix(b"\n")
                first = False
            name = os.fsdecode(raw)
            if name:
                commits.setdefault(name, sha)
                for parent in PurePosixPath(name).parents:
                    commits.setdefault(parent.as_posix(), sha)
            position += 1
    return commits


def plain_history_path(path: str) -> bool:
    """Git pathspec 元字符保持原查询语义，不把 literal 文件名当作 pattern 结果。"""
    return not path.startswith(":") and not any(char in path for char in "*?[\\")
