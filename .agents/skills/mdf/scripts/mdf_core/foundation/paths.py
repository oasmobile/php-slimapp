import os
from pathlib import Path
from typing import Any

from mdf_core.foundation.constants import MANAGED_ROOTS
from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.yamlutil import parse_yaml


def manifest_path(repo: Path) -> Path:
    return repo / ".mdf" / "manifest.yaml"


def path_stays_in_repo(repo: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(repo)
    except ValueError:
        return False
    return True


def is_local_artifact_root(repo: Path, path: Path) -> bool:
    return path in {repo / ".mdf" / name for name in ("logs", "reports", "tmp")}


def managed_symlinks(repo: Path) -> list[Path]:
    """检查托管路径；本地日志、报告与临时目录只检查目录本身，不递归扫描产物。"""
    found: set[Path] = set()
    local_artifacts = {repo / ".mdf" / name for name in ("logs", "reports", "tmp")}
    for name in MANAGED_ROOTS:
        root = repo / name
        if root.is_symlink():
            found.add(root)
            continue
        if root.is_dir() and path_stays_in_repo(repo, root):
            for directory, dirs, files in os.walk(root):
                parent = Path(directory)
                found.update(parent / name for name in (*dirs, *files) if (parent / name).is_symlink())
                dirs[:] = [name for name in dirs if parent / name not in local_artifacts]
    return sorted(found)


def ensure_safe_managed_paths(repo: Path) -> None:
    unsafe = [path for path in managed_symlinks(repo) if not is_local_artifact_root(repo, path)]
    if unsafe:
        raise MDFError(
            "MDF-managed paths must not be symbolic links",
            code="managed_symlink",
            details={
                "paths": [path.relative_to(repo).as_posix() for path in unsafe]
            },
        )


def load_manifest(repo: Path) -> dict[str, Any]:
    path = manifest_path(repo)
    if not path.is_file():
        raise MDFError("Missing .mdf/manifest.yaml", code="not_initialized")
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        raise MDFError(
            "MDF manifest must be a regular repository file",
            code="managed_symlink",
        )
    return parse_yaml(path.read_text(encoding="utf-8"))


def relative(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo).as_posix()
