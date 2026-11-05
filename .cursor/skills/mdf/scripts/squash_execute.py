"""执行已定型的 squash 计划；失败保留现场，以 JSON 返回完整 Git 调用记录。"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace import squash
from mdf_core.lifecycle.roster import parse_role_branch
from mdf_core.workspace.gitutil import branch_details


def execute(repo: Path, plan: dict, verify_only: bool, trace: list) -> dict:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True,
        )
        trace.append({"args": list(args), "exit_code": result.returncode,
                      "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise ValueError(f"Git 调用失败：{args[0]}")
        return result.stdout if "-z" in args else result.stdout.strip()

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def commit(value: str) -> str:
        require(isinstance(value, str), "commit 必须为完整 hash")
        resolved = git("rev-parse", "--verify", f"{value}^{{commit}}")
        require(resolved == value, "计划须使用完整 commit hash")
        return resolved

    require(repo.is_dir(), "目标目录不存在")
    require(Path(git("rev-parse", "--show-toplevel")).resolve() == repo,
            "目标必须为 Git 根")
    start = commit(plan["start_commit"])
    old_tip = commit(plan["old_tip"])
    branch = plan["branch"]
    require(git("branch", "--show-current") == branch
            and (branch == "planning"
                 or branch_details(branch)["supported"]
                 or parse_role_branch(branch)),
            "当前分支须为计划中的交付、角色或 planning 分支")

    def verify() -> dict:
        require(not git("diff", old_tip, "HEAD", "--"), "最终 tree 与旧 tip 不一致")
        git("merge-base", "--is-ancestor", start, "HEAD")
        require(not git("status", "--porcelain", "--untracked-files=no"),
                "已跟踪工作区不干净")
        return {"head": git("rev-parse", "HEAD"), "old_tip": old_tip,
                "tree_equal": True, "start_is_ancestor": True, "clean": True}

    if verify_only:
        return verify()
    require(git("rev-parse", "HEAD") == old_tip, "HEAD 已变化，须重新分析计划")
    require(not git("status", "--porcelain", "--untracked-files=no"),
            "已跟踪工作区不干净")
    floor = commit(plan["floor"])
    git("merge-base", "--is-ancestor", start, floor)
    git("merge-base", "--is-ancestor", floor, old_tip)
    safe = squash.check(repo)
    git("merge-base", "--is-ancestor", safe["floor"], floor)
    if safe["noop"]:
        return {**verify(), "noop": True}
    require(floor != old_tip, "可改写区间为空")
    segments = plan["segments"]
    require(isinstance(segments, list) and bool(segments), "段界列表不能为空")
    previous = floor
    for segment in segments:
        tip = commit(segment["tip"])
        require(isinstance(segment["message"], str) and bool(segment["message"].strip()),
                "每段须有已定型 message")
        git("merge-base", "--is-ancestor", previous, tip)
        git("merge-base", "--is-ancestor", tip, old_tip)
        require(previous != tip, "段界须严格递增")
        previous = tip
    require(previous == old_tip, "末段须为旧 tip")
    email = git("var", "GIT_COMMITTER_IDENT").split("<", 1)[1].split(">", 1)[0]
    owners = git("log", "--format=%ae%n%ce", f"{floor}..{old_tip}").splitlines()
    require(bool(email) and all(owner == email for owner in owners), "区间含他人 commit")
    rewritten = set(git("rev-list", f"{floor}..{old_tip}").splitlines())
    published = set(git("rev-list", "--remotes").splitlines())
    require(not rewritten.intersection(published), "区间含远程引用已发布的 commit")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for segment in segments:
        tracked = git("ls-tree", "-r", "--name-only", "-z", segment["tip"]).split("\0")
        require(not any(
            u and t and (u == t or u.startswith(t + "/") or t.startswith(u + "/"))
            for u in untracked for t in tracked
        ), "未跟踪文件与段界路径冲突，须先明确处理")
    require(not git("rev-list", "--min-parents=2", f"{floor}..{old_tip}"), "不得改写 merge commit")
    if len(segments) == len(rewritten):
        require(isinstance(plan.get("noop_reason"), str) and bool(plan["noop_reason"].strip()),
                "保留全部提交须说明语义分段理由")
        squash.record_analysis(repo, branch, old_tip, reason=plan["noop_reason"])
        return {**verify(), "noop": True}
    require(len(segments) < len(rewritten), "squash 不得增加 commit 数量")
    previous = floor
    for segment in segments:
        require(bool(git("diff", "--name-only", previous, segment["tip"], "--")),
                "需要重建的每段 tree 须有变化")
        previous = segment["tip"]
    git("reset", "--soft", floor)
    heads = []
    for segment in segments:
        git("restore", f"--source={segment['tip']}", "--staged", "--worktree", ".")
        git("commit", "-m", segment["message"])
        heads.append(git("rev-parse", "HEAD"))
    result = verify()
    squash.record_analysis(repo, branch, result["head"], reason="已按分析计划完成分段 squash")
    return {**result, "commits": heads}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--plan-file", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    trace: list = []
    try:
        if args.check:
            if args.plan_file or args.verify_only:
                raise ValueError("--check 不与执行或验证选项混用")
            result = squash.check(args.repo.resolve())
        else:
            if not args.plan_file:
                raise ValueError("需要 --plan-file 或 --check")
            plan = json.loads(args.plan_file.read_text(encoding="utf-8"))
            result = execute(args.repo.resolve(), plan, args.verify_only, trace)
    except (ValueError, KeyError, TypeError, OSError, MDFError) as error:
        print(json.dumps({"ok": False, "error": str(error), "trace": trace}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result, "trace": trace}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
