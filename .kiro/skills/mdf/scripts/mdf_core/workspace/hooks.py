"""manifest hook 配置与 command/rule 执行。"""

import os
from pathlib import Path
import sys

from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.paths import load_manifest, path_stays_in_repo
from mdf_core.execution.run_logs import stream_child


HOOK_NAME = "post-gitflow-start"
FINISH_HOOK = "pre-gitflow-finish"


def validate_hooks(manifest):
    hooks = manifest.get("hooks", {})
    if not isinstance(hooks, dict):
        raise MDFError("hooks 必须为 mapping", code="invalid_hooks")
    for name, entry in hooks.items():
        if name not in (HOOK_NAME, FINISH_HOOK):
            raise MDFError(f"未知 hook：{name}", code="invalid_hooks")
        if not isinstance(entry, dict) or set(entry) != {"type", "path"}:
            raise MDFError("hook 必须只含 type 与 path", code="invalid_hooks")
        if entry["type"] not in ("command", "rule"):
            raise MDFError("hook type 必须为 command 或 rule", code="invalid_hooks")
        raw = entry["path"]
        if (not isinstance(raw, str) or not raw.strip()
                or Path(raw).is_absolute() or ".." in Path(raw).parts):
            raise MDFError("hook path 必须为 repo root 相对路径", code="invalid_hooks")
    return hooks


def post_gitflow_start(old_worktree, new_worktree):
    return run_hook(
        new_worktree, HOOK_NAME,
        context={"old_worktree": str(old_worktree), "new_worktree": str(new_worktree)},
        env={"MDF_OLD_WORKTREE": str(old_worktree), "MDF_NEW_WORKTREE": str(new_worktree)},
        continuation="不影响 start",
    )


def run_hook(repo, name, *, context, env, continuation):
    try:
        entry = validate_hooks(load_manifest(repo)).get(name)
        if entry is None:
            return None
        print(f"开始执行 hook {name}：{entry['path']}；cwd={repo}",
              file=sys.stderr, flush=True)
        path = repo / entry["path"]
        if not path_stays_in_repo(repo, path) or not path.is_file():
            raise MDFError("hook path 必须指向当前 worktree 内的文件", code="invalid_hooks")
        result = {
            "name": name, **entry, "cwd": str(repo), **context,
        }
        if entry["type"] == "rule":
            return {**result, "status": "pending"}
        try:
            returncode = stream_child(
                [str(path.resolve())], cwd=repo, env={**os.environ, **env},
            )
            result.update(status="success" if returncode == 0 else "failed",
                          returncode=returncode)
        except OSError as exc:
            result.update(status="failed", error=str(exc))
        print(f"hook {name} 执行结束：{result['status']}；"
              f"失败仅汇报，{continuation}", file=sys.stderr, flush=True)
        return result
    except MDFError as exc:
        print(f"hook {name} 执行结束：失败：{exc}；{continuation}", file=sys.stderr, flush=True)
        return {"name": name, "status": "failed", "error": str(exc)}
