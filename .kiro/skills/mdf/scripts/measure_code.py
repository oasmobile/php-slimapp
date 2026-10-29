"""只读测量代码文件与完整 package，提供硬限制及拆分目标证据，不运行项目命令。"""
import argparse
import json
import sys
from pathlib import Path

# 即使调用方忘记 -B，也不得在已安装 Skill 的 worktree 中创建 bytecode。
sys.dont_write_bytecode = True

from mdf_core.execution.modules import load_modules, parse_modules
from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.paths import path_stays_in_repo
from mdf_core.inspection.code_size import code_size_measurements, is_source
from mdf_core.foundation.yamlutil import parse_yaml
from mdf_core.workspace.gitutil import require_git_root, repo_path, run


def measure(repo, paths, ref=None, file_targets=(), package_targets=(), policy_ref=None):
    require_git_root(repo)

    def resolve(value):
        return run(["git", "rev-parse", "--verify", "--end-of-options", f"{value}^{{commit}}"], cwd=repo).stdout.strip()

    if policy_ref is not None:
        policy_ref = resolve(policy_ref)
        raw = run(["git", "show", f"{policy_ref}:.mdf/modules.yaml"], cwd=repo).stdout
        config = parse_modules(parse_yaml(raw))
    else:
        config = load_modules(repo)
    if any(type(value) is not int or value <= 0 for value in (*file_targets, *package_targets)):
        raise MDFError("原拆分目标必须是正整数", code="invalid_target")
    scopes = []
    for raw in paths:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or not raw.strip():
            raise MDFError("--path 必须是仓库相对文件或目录", code="invalid_path")
        scopes.append(path.as_posix())

    def selected(name):
        return not scopes or any(scope == "." or name == scope or name.startswith(scope.rstrip("/") + "/")
                                 for scope in scopes)

    if ref is not None:
        ref = resolve(ref)
        entries = run(["git", "ls-tree", "-r", "-z", "--full-tree", ref], cwd=repo).stdout.split("\0")
        names = [entry.split("\t", 1)[1] for entry in entries
                 if entry and entry.split("\t", 1)[0].startswith(("100644 ", "100755 "))]
    else:
        names = run(["git", "ls-files", "-z"], cwd=repo).stdout.split("\0")
        names = [name for name in names if name and (repo / name).is_file()
                 and not (repo / name).is_symlink() and path_stays_in_repo(repo, repo / name)]
    names = [name for name in names if is_source(Path(name))]
    ignored = [name for name in names if selected(name) and config.is_ignored(name)]
    counts = {}
    for name in names:
        if not selected(name) or config.is_ignored(name):
            continue
        content = (run(["git", "show", f"{ref}:{name}"], cwd=repo).stdout if ref is not None
                   else (repo / name).read_text(encoding="utf-8"))
        counts[name] = len(content.splitlines())
    result = code_size_measurements(counts, names, config)
    for key, targets in (("files", file_targets), ("packages", package_targets)):
        if targets:
            for item in result[key]:
                item["required_split_targets"] = list(targets)
                item["within_required_split_targets"] = all(item["value"] <= target for target in targets)
    return {"source_ref": ref, "policy_ref": policy_ref, "policy": ".mdf/modules.yaml",
            "ignored": sorted(ignored), **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--ref", help="源码 Git commit/ref；省略时读取工作区")
    parser.add_argument("--policy-ref", help="显式策略快照；只接受当前契约格式，不探测或转换旧格式")
    parser.add_argument("--file-target", action="append", type=int, default=[], help="原文件拆分目标；可重复")
    parser.add_argument("--package-target", action="append", type=int, default=[], help="原 package 拆分目标；可重复")
    args = parser.parse_args()
    try:
        result = measure(repo_path(args.repo), args.path, args.ref, args.file_target,
                         args.package_target, args.policy_ref)
    except (MDFError, OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
