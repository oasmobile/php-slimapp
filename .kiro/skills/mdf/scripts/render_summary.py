"""把已填写的总结正文固化为完整 HTML；保留命令日志，不替代语义审阅。"""
import argparse
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path

from mdf_core.cli import _failure
from mdf_core.foundation.constants import MARKER_RE
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.workspace.gitutil import (
    branch_details,
    current_branch,
    git_in_progress_head,
    repo_path,
    require_git_root,
    run,
    unreleased_slug,
)
from mdf_core.documents.html_documents import DocumentParser, render_document, visible_text
from mdf_core.foundation.paths import ensure_safe_managed_paths, load_manifest, relative
from mdf_core.execution.run_logs import RunLog
from mdf_core.inspection.validate_links import require_existing_local_links
from mdf_core.foundation.yamlutil import read_frontmatter

SECTIONS = ("交付范围与结果", "完整交付过程", "设计决策与取舍", "开发与测试实现",
            "偏差与范围变化", "审查与验证证据", "交付与后续事项")


def render_summary(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    ensure_safe_managed_paths(repo)
    manifest = load_manifest(repo)
    if manifest.get("state") != "ready":
        raise MDFError("总结生成需要 ready 仓库", code="manifest_not_ready")
    if git_in_progress_head(repo) is not None:
        raise MDFError("当前有未结束的 Git 操作，保留现场", code="dirty_worktree")
    branch = current_branch(repo)
    details = branch_details(branch)
    if not details["supported"]:
        raise MDFError("总结生成只用于 owner 交付分支", code="unsupported_branch")
    common = Path(run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo).stdout.strip())
    if (common / "mdf/finish" / f"{branch}.json").exists():
        raise MDFError("已开始发布，不得改写交付总结", code="publish_state_changed")
    root = repo / "changes/unreleased" / unreleased_slug(details)
    if details["kind"] in {"release", "hotfix"}:
        released = repo / "changes" / details["version"]
        if (released / "CHANGE.md").is_file():
            metadata, _ = read_frontmatter(released / "CHANGE.md")
            if (metadata.get("version") != details["version"] or metadata.get("source_branch") != branch
                    or metadata.get("change_kind") != details["kind"]
                    or not isinstance(manifest.get("versioning"), dict)
                    or manifest["versioning"].get("latest_release") != details["version"]):
                raise MDFError("版本目录与当前收口不一致，保留现场", code="publish_state_changed")
            root = released
    target = root / "delivery-summary.html"
    source = Path(args.body_file).expanduser()
    if source.is_symlink() or not source.is_file():
        raise MDFError("总结正文必须为普通 HTML 文件", code="invalid_path")
    content = source.read_text(encoding="utf-8")
    prose = re.sub(r"<(pre|code)\b[^>]*>.*?</\1\s*>", "", content, flags=re.DOTALL | re.IGNORECASE)
    if MARKER_RE.search(prose) or re.search(
        r"<!doctype|<(?:html|head|body|main|script|style)\b", content, re.IGNORECASE
    ):
        raise MDFError("总结输入须为已填好的 HTML 正文，不得含占位符、文档外框或 script/style",
                       code="invalid_summary")
    parser = DocumentParser()
    parser.feed("<main>" + content + "</main>")
    text = visible_text("<main>" + content + "</main>")
    if not re.search(r"(?m)^# \S", text):
        raise MDFError("总结缺少非空 h1 标题", code="invalid_summary")
    for heading in SECTIONS:
        match = re.search(rf"(?m)^## {re.escape(heading)}\s*$", text)
        if not match:
            raise MDFError(f"总结缺少章节：{heading}", code="invalid_summary")
        rest = text[match.end():]
        following = re.search(r"(?m)^#{1,2} \S", rest)
        section = rest[:following.start()] if following else rest
        if not section.strip() or heading not in {label for _, label in parser.outline}:
            raise MDFError(f"总结章节为空或缺少锚点：{heading}", code="invalid_summary")
    anchors = [anchor for anchor, _ in parser.outline]
    if len(anchors) != len(set(anchors)):
        raise MDFError("总结章节锚点重复", code="invalid_summary")
    title = next(line[2:] for line in text.splitlines() if line.startswith("# "))
    document = render_document(content, title)
    root.mkdir(parents=True, exist_ok=True)
    candidate = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".html", dir=root,
                                         prefix=".summary-", delete=False) as stream:
            candidate = Path(stream.name)
            stream.write(document)
        require_existing_local_links(repo, [candidate])
        os.replace(candidate, target)
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
    return {"ok": True, "operation": "render-summary", "path": relative(repo, target), "sections": len(parser.outline)}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    log = RunLog(["render-summary", *argv])
    code = 1
    with log:
        try:
            parser = argparse.ArgumentParser(description="生成交付总结的完整 HTML")
            parser.add_argument("--repo", required=True)
            parser.add_argument("--body-file", required=True)
            args = parser.parse_args(argv)
            emit({**render_summary(args), "log": str(log.path)})
            code = 0
        except MDFError as exc:
            code = _failure(exc.code, str(exc), exc.details, log)
        except (OSError, UnicodeError) as exc:
            traceback.print_exc(file=sys.stderr)
            code = _failure("operation_failed", str(exc), None, log)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
            raise
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            code = _failure("internal_error", str(exc), None, log)
        finally:
            log.finish(code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
