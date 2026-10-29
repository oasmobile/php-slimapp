"""项目阶段 rule 的配置校验与原文加载；不执行文件。"""

import hashlib
import json
from pathlib import Path

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import repo_path, require_git_root, run
from mdf_core.foundation.paths import load_manifest, path_stays_in_repo


STAGES = ("design", "code-review")


def validate_rules(manifest):
    rules = manifest.get("rules", {})
    if not isinstance(rules, dict):
        raise MDFError("rules 必须为 mapping", code="invalid_rules")
    for stage, raw in rules.items():
        if stage not in STAGES:
            raise MDFError(f"未知 rule 阶段：{stage}", code="invalid_rules")
        if (not isinstance(raw, str) or not raw.strip()
                or Path(raw).is_absolute() or ".." in Path(raw).parts):
            raise MDFError(f"rules.{stage} 必须为非空 repo root 相对路径", code="invalid_rules")
    return rules


def load_project_rule(repo, manifest, stage):
    if stage not in STAGES:
        raise MDFError(f"未知 rule 阶段：{stage}", code="invalid_rules")
    raw = validate_rules(manifest).get(stage)
    if raw is None:
        return None
    path = repo / raw
    try:
        parts = path.relative_to(repo).parts
        if (any(repo.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1))
                or not path_stays_in_repo(repo, path) or not path.is_file()):
            raise ValueError("必须为 worktree 内的普通文件，路径不得含 symlink")
        relative = path.relative_to(repo).as_posix()
        tracked = run(
            ["git", "ls-files", "--error-unmatch", "--", f":(literal){relative}"],
            cwd=repo, check=False,
        )
        if tracked.returncode:
            raise ValueError("文件必须 Git tracked")
        data = path.read_bytes()
        content = data.decode("utf-8")
        if not content.strip():
            raise ValueError("文件内容不得为空")
    except (OSError, UnicodeError, ValueError) as exc:
        raise MDFError(f"rules.{stage}：{raw}：{exc}", code="invalid_rules") from exc
    return {"path": relative, "content": content, "sha256": hashlib.sha256(data).hexdigest()}


def command_project_rules(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    rule = load_project_rule(repo, load_manifest(repo), args.stage)
    print(json.dumps({"stage": args.stage, "project_rule": rule}, ensure_ascii=False))
