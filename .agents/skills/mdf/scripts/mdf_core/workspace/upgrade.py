"""Install-tree upgrade for the published MDF skill."""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from mdf_core.foundation.constants import MDF_BLOCK_END, MDF_BLOCK_START
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import repo_path, require_git_root
from mdf_core.foundation.paths import relative

DEFAULT_SKILL_SOURCE = "http://10.1.5.65:8929/mars/mdf"
KNOWN_SKILL_DIRS = (
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".cursor/skills",
    ".kiro/skills",
    ".openclaw/skills",
)
SOURCE_SKILL = "skills/mdf"
AGENTS_TEMPLATE = Path("assets") / "templates" / "agents-managed-block.md"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


def _run(
    args: list[str], cwd: Path | None = None, *, text: bool = True
):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        args, cwd=cwd, text=text, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False, env=env,
    )


def _git_text(args: list[str], cwd: Path) -> str:
    completed = _run(args, cwd)
    if completed.returncode:
        raise MDFError(
            completed.stderr.strip() or f"Command failed: {' '.join(args)}",
            code="command_failed",
        )
    return completed.stdout.strip()


def _clone(source: str, dest: Path) -> None:
    completed = _run(["git", "clone", "--depth", "1", "--", source, str(dest)])
    if completed.returncode:
        raise MDFError(
            completed.stderr.strip() or f"git clone failed: {source}",
            code="upgrade_clone_failed",
        )


def _archive_skill(clone: Path, commit: str) -> bytes:
    completed = _run(
        ["git", "archive", "--format=tar", f"{commit}:{SOURCE_SKILL}"],
        clone, text=False,
    )
    if completed.returncode:
        err = completed.stderr.decode().strip() if completed.stderr else ""
        raise MDFError(err or "git archive failed", code="upgrade_archive_failed")
    return completed.stdout


def _extract_tar(data: bytes, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tar:
        kwargs: dict[str, object] = {}
        if sys.version_info >= (3, 12):
            kwargs["filter"] = "data"
        tar.extractall(dest, **kwargs)


def _read_version(skill: Path) -> str | None:
    path = skill / "references" / ".version"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    text = lines[0].strip() if lines else ""
    return text or None


def _installed_skills(repo: Path) -> list[Path]:
    found: list[Path] = []
    for directory in KNOWN_SKILL_DIRS:
        skill = repo / directory / "mdf"
        if not skill.exists() and not skill.is_symlink():
            continue
        if skill.is_symlink() or not skill.is_dir():
            raise MDFError(
                f"Installed mdf is not a directory: {relative(repo, skill)}",
                code="upgrade_not_dir",
            )
        found.append(skill)
    if not found:
        raise MDFError(
            "No installed mdf skill found in Agent skills directories",
            code="upgrade_no_install",
        )
    return found


def _write_version(skill: Path, commit: str) -> None:
    path = skill / "references" / ".version"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{commit}\n", encoding="utf-8")


def _agents_template(skill_root: Path) -> str:
    path = skill_root / AGENTS_TEMPLATE
    if not path.is_file():
        raise MDFError(
            "Upstream is missing assets/templates/agents-managed-block.md",
            code="upgrade_missing_agents_template",
        )
    return path.read_text(encoding="utf-8").strip()


def _agents_file_state(repo: Path) -> str:
    path = repo / "AGENTS.md"
    if not path.exists():
        return "absent"
    if path.is_symlink() or not path.is_file():
        raise MDFError(
            "AGENTS.md must be a regular repository file",
            code="upgrade_agents_not_file",
        )
    text = path.read_text(encoding="utf-8")
    starts = text.count(MDF_BLOCK_START)
    ends = text.count(MDF_BLOCK_END)
    if starts == 0 and ends == 0:
        return "no_block"
    if (
        starts == 1
        and ends == 1
        and text.index(MDF_BLOCK_START) < text.index(MDF_BLOCK_END)
    ):
        return "present"
    raise MDFError(
        "AGENTS.md 的 MDF 标记格式错误或重复",
        code="invalid_managed_block",
    )


def _replace_managed_block(text: str, block: str) -> str:
    start = text.index(MDF_BLOCK_START)
    end = text.index(MDF_BLOCK_END) + len(MDF_BLOCK_END)
    return text[:start] + block + text[end:]


def _plan_agents(
    repo: Path, skill_root: Path
) -> tuple[dict[str, str], str | None]:
    state = _agents_file_state(repo)
    if state in {"absent", "no_block"}:
        return {"path": "AGENTS.md", "action": "skip", "reason": state}, None
    block = _agents_template(skill_root)
    current = (repo / "AGENTS.md").read_text(encoding="utf-8")
    updated = _replace_managed_block(current, block)
    if updated == current:
        return {"path": "AGENTS.md", "action": "unchanged"}, None
    return {"path": "AGENTS.md", "action": "update"}, updated


def _has_commit(clone: Path, commit: str) -> bool:
    probe = ["git", "cat-file", "-e", f"{commit}^{{commit}}"]
    return _run(probe, clone).returncode == 0


def _ensure_commit(clone: Path, commit: str) -> bool:
    if not _has_commit(clone, commit):
        _run(["git", "fetch", "--unshallow"], clone)
    return _has_commit(clone, commit)


def _skill_path(raw: str) -> str:
    prefix = f"{SOURCE_SKILL}/"
    if raw.startswith(prefix):
        return raw[len(prefix) :]
    if raw == SOURCE_SKILL:
        return "."
    return raw


def _changed_files(clone: Path, old: str, new: str) -> list[dict[str, str]]:
    text = _git_text(
        ["git", "diff", "--name-status", old, new, "--", SOURCE_SKILL],
        clone,
    )
    files: list[dict[str, str]] = []
    for line in text.splitlines():
        status, _, rest = line.partition("\t")
        path = rest.split("\t")[-1] if rest else ""
        if not status or not path:
            continue
        files.append({"status": status, "path": _skill_path(path)})
    return files


def _skill_history(
    clone: Path, old: str | None, new: str
) -> dict[str, object]:
    result: dict[str, object] = {
        "from": old,
        "to": new,
        "status": "ok",
        "commits": [],
        "files": [],
    }
    if not old:
        result["status"] = "no_current_version"
        return result
    if old == new:
        result["status"] = "same"
        return result
    if not _COMMIT_RE.fullmatch(old) or not _ensure_commit(clone, old):
        result["status"] = "unknown_base"
        return result
    log = _git_text(
        ["git", "log", "--format=%H%x09%s", f"{old}..{new}", "--", SOURCE_SKILL],
        clone,
    )
    commits: list[dict[str, str]] = []
    for line in log.splitlines():
        commit, _, subject = line.partition("\t")
        if commit:
            commits.append({"commit": commit, "subject": subject})
    result["commits"] = commits
    result["files"] = _changed_files(clone, old, new)
    return result


def _commit_plan(
    targets: list[dict[str, str | None]],
    agents: dict[str, str],
    new_commit: str,
) -> dict[str, object]:
    paths = [item["path"] for item in targets if item.get("path")]
    if agents.get("action") == "update" and agents.get("path"):
        paths.append(agents["path"])
    return {
        "paths": paths,
        "message": f"chore(mdf): 升级已安装 Skill 到 {new_commit[:12]}",
    }


def _commit_upgrade(repo: Path, plan: dict[str, object]) -> dict[str, object]:
    paths = [path for path in plan["paths"] if isinstance(path, str)]
    message = str(plan["message"])
    result: dict[str, object] = {"paths": paths, "message": message}
    if not paths:
        result.update(action="none", reason="no_paths")
        return result
    added = _run(["git", "add", "-A", "--", *paths], repo)
    if added.returncode:
        raise MDFError(
            added.stderr.strip() or "git add failed",
            code="upgrade_commit_failed",
        )
    diff = _run(["git", "diff", "--cached", "--quiet", "--", *paths], repo)
    if diff.returncode == 0:
        result.update(action="none", reason="unchanged")
        return result
    if diff.returncode != 1:
        raise MDFError(
            diff.stderr.strip() or "git diff failed",
            code="upgrade_commit_failed",
        )
    created = _run(
        ["git", "commit", "--only", "-m", message, "--", *paths], repo
    )
    if created.returncode:
        raise MDFError(
            created.stderr.strip() or created.stdout.strip() or "git commit failed",
            code="upgrade_commit_failed",
        )
    result["action"] = "created"
    result["commit"] = _git_text(["git", "rev-parse", "HEAD"], repo)
    return result


def _collect_history(
    clone: Path,
    targets: list[dict[str, str | None]],
    new: str,
) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    index: dict[str | None, list[str]] = {}
    for target in targets:
        old = target["current_commit"]
        path = target["path"] or ""
        if old not in index:
            index[old] = []
            item = _skill_history(clone, old, new)
            item["targets"] = index[old]
            groups.append(item)
        index[old].append(path)
    return groups


def _replace_skill(dest: Path, payload: Path, commit: str) -> None:
    parent = dest.parent
    staging = parent / ".mdf-skill-new"
    backup = parent / ".mdf-skill-old"
    if staging.exists():
        shutil.rmtree(staging)
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(payload, staging)
    _write_version(staging, commit)
    dest.rename(backup)
    try:
        staging.rename(dest)
    except OSError:
        backup.rename(dest)
        raise
    shutil.rmtree(backup)


def _fetch(source: str) -> tuple[str, Path, tempfile.TemporaryDirectory[str]]:
    temp = tempfile.TemporaryDirectory()
    clone = Path(temp.name) / "source"
    try:
        _clone(source, clone)
        commit = _git_text(["git", "rev-parse", "HEAD"], clone)
        skill = clone / SOURCE_SKILL
        if not skill.is_dir():
            raise MDFError(
                f"Upstream is missing {SOURCE_SKILL}",
                code="upgrade_missing_skill",
            )
    except Exception:
        temp.cleanup()
        raise
    return commit, clone, temp

def command_upgrade(args: argparse.Namespace) -> None:
    repo = repo_path(args.repo)
    require_git_root(repo)
    source = args.source
    if not args.dry_run and not _COMMIT_RE.fullmatch(args.expected_commit or ""):
        raise MDFError("替换需要预览确认的完整 commit", code="missing_expected_commit")
    installs = _installed_skills(repo)
    commit, clone, temp = _fetch(source)
    try:
        if not args.dry_run and commit != args.expected_commit:
            raise MDFError("上游已变化，须重新预览并确认", code="upgrade_source_changed",
                           details={"expected": args.expected_commit, "actual": commit})
        targets = [
            {
                "path": relative(repo, skill),
                "current_commit": _read_version(skill),
            }
            for skill in installs
        ]
        agents, agents_text = _plan_agents(repo, clone / SOURCE_SKILL)
        plan = _commit_plan(targets, agents, commit)
        payload = {
            "ok": True,
            "operation": "upgrade",
            "dry_run": bool(args.dry_run),
            "source": source,
            "new_commit": commit,
            "targets": targets,
            "history": _collect_history(clone, targets, commit),
            "agents": agents,
            "commit": {"action": "planned", **plan},
        }
        if args.dry_run:
            emit(payload)
            return
        archive = _archive_skill(clone, commit)
        with tempfile.TemporaryDirectory() as extracted_root:
            extracted = Path(extracted_root) / "skill"
            _extract_tar(archive, extracted)
            if not (extracted / "SKILL.md").is_file():
                raise MDFError(
                    "Archived skill is missing SKILL.md",
                    code="upgrade_missing_skill",
                )
            for skill in installs:
                _replace_skill(skill, extracted, commit)
        if agents_text is not None:
            (repo / "AGENTS.md").write_text(agents_text, encoding="utf-8")
        payload["replaced"] = [item["path"] for item in targets]
        payload["commit"] = _commit_upgrade(repo, plan)
        emit(payload)
    finally:
        temp.cleanup()
