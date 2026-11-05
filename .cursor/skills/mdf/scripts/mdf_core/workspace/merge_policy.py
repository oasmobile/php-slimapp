"""PR mode 配置、路径例外与 Git 历史检查。"""
from pathlib import Path
from fnmatch import fnmatchcase

from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.paths import load_manifest, manifest_path
from mdf_core.foundation.yamlutil import parse_yaml
from mdf_core.workspace.gitutil import run

HOSTS = (".agents/", ".claude/", ".codex/", ".cursor/", ".kiro/", ".openclaw/")


def git(repo, *args, check=True):
    return run(["git", *args], cwd=repo, check=check)


def config(manifest):
    value = manifest.get("closeout", {"mode": "local"})
    if (not isinstance(value, dict) or set(value) - {"mode", "provider", "trivial_paths"}
            or value.get("mode") not in ("local", "pr")
            or (value.get("mode") == "pr" and value.get("provider") not in ("github", "gitlab"))
            or ("provider" in value and value["provider"] not in ("github", "gitlab"))):
        raise MDFError("closeout 需要 mode: local|pr；pr 需要 provider: github|gitlab", code="invalid_closeout")
    patterns = value.get("trivial_paths")
    if patterns is not None and (not isinstance(patterns, list)
                                 or any(not isinstance(p, str) or not p.strip() for p in patterns)):
        raise MDFError("closeout.trivial_paths 必须为非空路径 pattern 的列表", code="invalid_closeout")
    if "trivial_paths" in value and patterns is None:
        raise MDFError("closeout.trivial_paths 不能为 null", code="invalid_closeout")
    return dict(value)


def manifest_at(repo, ref):
    return parse_yaml(git(repo, "show", f"{sha(repo, ref)}:.mdf/manifest.yaml").stdout)


def configured(repo, ref=None):
    if ref is not None:
        return config(manifest_at(repo, ref))
    return config(load_manifest(repo)) if manifest_path(repo).is_file() else {"mode": "local"}


def sha(repo, ref):
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.strip()


def ancestor(repo, older, newer):
    return git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def maintenance(path):
    return path == "AGENTS.md" or path.startswith((".mdf/", *HOSTS))


def trivial(repo, path):
    patterns = configured(repo).get("trivial_paths")
    return maintenance(path) if patterns is None else any(fnmatchcase(path, p) for p in patterns)


def trivial_commits(repo, before, after):
    """逐笔检查全部独有历史，避免最终 diff 或 revert 掩盖 non-trivial。"""
    commits = git(repo, "rev-list", f"{before}..{after}").stdout.split()
    return all(all(trivial(repo, p) for p in commit_paths(repo, c)) for c in commits)


def document(path):
    return maintenance(path) or path.startswith(("docs/", "changes/")) or ("/" not in path and path.endswith(".md"))


def paths(repo, before, after):
    return [p for p in git(repo, "diff", "--no-renames", "--name-only", "-z", before, after).stdout.split("\0") if p]


def commit_paths(repo, commit):
    parents = git(repo, "show", "-s", "--format=%P", commit).stdout.split()
    if len(parents) > 2:
        raise MDFError("不支持 octopus merge 的例外判定", code="unknown_merge")
    if len(parents) == 2:
        raw = git(repo, "show", "--remerge-diff", "--format=", "--name-only", "--no-renames", "-z", commit).stdout
        return [p for p in raw.split("\0") if p]
    if parents:
        return paths(repo, parents[0], commit)
    return [p for p in git(repo, "ls-tree", "-rz", "--name-only", commit).stdout.split("\0") if p]


def planning_only(repo, before, after):
    if not all(document(p) for p in paths(repo, before, after)):
        return False
    commits = git(repo, "rev-list", f"{before}..{after}").stdout.split()
    return all(all(document(p) for p in commit_paths(repo, commit)) for commit in commits)


def require_merge(repo, source, target):
    if (target not in {"master", "develop"} or not manifest_path(repo).is_file()
            or configured(repo, "HEAD")["mode"] != "pr"):
        return
    incoming = sha(repo, source)
    if ancestor(repo, incoming, "HEAD"):
        return
    master = git(repo, "rev-parse", "--verify", "refs/heads/master", check=False)
    if target == "develop" and not master.returncode and ancestor(repo, incoming, master.stdout.strip()):
        return
    if (target == "develop" and source in {"planning", "refs/heads/planning"}
            and planning_only(repo, "HEAD", incoming)):
        return
    raise MDFError(f"PR mode 禁止直接合入 {target}；请创建 PR/MR", code="pr_required")
