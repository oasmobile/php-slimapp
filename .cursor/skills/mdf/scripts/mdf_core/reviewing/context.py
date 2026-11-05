"""从固定 Git 对象提取审查上下文，不读取开发机配置。"""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from mdf_core.reviewing.scope import review_changes, source_modules
from mdf_core.foundation.errors import MDFError, emit
from mdf_core.foundation.textutil import stable_semver
from mdf_core.lifecycle.delivery_state import read_json
from mdf_core.lifecycle.roster import require_roster
from mdf_core.workspace.gitutil import branch_details, repo_path, require_git_root, unreleased_slug
from mdf_core.workspace.merge_policy import ancestor, git, manifest_at, sha


def blob(repo, ref, path, *, required=True):
    parts = PurePosixPath(path).parts
    if not parts or path.startswith("/") or ".." in parts:
        raise MDFError("审查材料路径必须位于仓库内", code="invalid_review_context")
    entry = git(repo, "ls-tree", ref, "--", f":(literal){path}").stdout
    if not entry:
        if required:
            raise MDFError(f"固定提交缺少 {path}", code="missing_review_artifact")
        return None
    if not entry.startswith(("100644 blob ", "100755 blob ")):
        raise MDFError(f"审查材料必须为普通文件：{path}", code="invalid_review_context")
    return git(repo, "show", f"{ref}:{path}").stdout


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def backmerge_identity(repo, source, head):
    version = source.removeprefix("codex/backmerge/")
    if stable_semver(version) is None:
        raise MDFError("回合 source 需要稳定版本号", code="invalid_review_context")
    tag = f"refs/tags/v{version}"
    if git(repo, "cat-file", "-t", tag).stdout.strip() != "tag":
        raise MDFError("回合审查需要 annotated 发布 tag", code="invalid_review_context")
    merged = sha(repo, tag)
    if not ancestor(repo, merged, head):
        raise MDFError("回合 source 未包含固定发布提交", code="invalid_review_context")
    history = git(repo, "rev-list", "--reverse", "--first-parent", "--parents", head).stdout.splitlines()
    for line in history:
        fields = line.split()
        if len(fields) == 3 and fields[2] == merged:
            return {"version": version, "merge_commit": merged, "base_commit": fields[1]}
    raise MDFError("无法定位引入发布提交的 no-ff 回合", code="invalid_review_base")


def context(repo, source=None, head=None, policy_ref=None, review_base=None, previous=None,
            *, against=None):
    if against is not None:
        if not against or any(value is not None for value in (source, head, policy_ref, review_base, previous)):
            raise MDFError('against 不能混用交付或增量参数', code='invalid_arguments')
        from mdf_core.reviewing.standalone import against_context
        return against_context(repo, against)
    elif not source or not head or not policy_ref:
        raise MDFError('需要 source/head/policy-ref 或 against', code='invalid_arguments')
    head, policy_ref = sha(repo, head), sha(repo, policy_ref)
    bases = git(repo, "merge-base", "--all", head, policy_ref, check=False).stdout.split()
    if len(bases) != 1:
        raise MDFError("source 与 target 需要唯一 merge-base", code="invalid_review_base")
    merge_base = bases[0]
    publication = backmerge_identity(repo, source, head) if source.startswith("codex/backmerge/") else None
    details = branch_details(source)
    if publication:
        details = {"supported": True, "kind": "backmerge", "version": publication["version"]}
    elif not details["supported"]:
        raise MDFError("需要 MDF 交付 source", code="unsupported_branch")
    folder = publication["version"] if publication else unreleased_slug(details)
    artifact_ref = publication["merge_commit"] if publication else head
    root = f"changes/unreleased/{folder}"
    if (details["kind"] in {"release", "hotfix", "backmerge"}
            and blob(repo, artifact_ref, f"changes/{folder}/delivery.json", required=False)):
        root = f"changes/{folder}"
    try:
        delivery = json.loads(blob(repo, artifact_ref, root + "/delivery.json"))
        roster = require_roster(delivery["roster"])
    except (ValueError, KeyError, TypeError) as exc:
        raise MDFError("交付身份或 roster 缺失", code="invalid_review_context") from exc
    if publication:
        published = branch_details(delivery.get("branch", ""))
        if published["kind"] not in {"release", "hotfix"} or published["version"] != publication["version"]:
            raise MDFError("发布 tag 的交付身份与回合版本不符", code="invalid_review_context")
        publication["source"] = delivery["branch"]
    elif delivery.get("branch") != source:
        raise MDFError("source 与 delivery.json 不符", code="invalid_review_context")
    manifest = manifest_at(repo, policy_ref)
    base = publication["base_commit"] if publication else delivery["start_commit"]
    if details["kind"] == "release":
        previous_version = manifest.get("versioning", {}).get("latest_release")
        if not previous_version:
            if previous is not None:
                base = previous.get("delivery_base")
                if not base:
                    raise MDFError("上轮报告缺少固定 delivery_base", code="invalid_previous_review")
            elif review_base:
                base = review_base
            else:
                raise MDFError("首次 release 需要显式确认的 --review-base", code="missing_review_base")
        else:
            base = sha(repo, f"refs/tags/v{previous_version}")
            if not ancestor(repo, base, policy_ref):
                raise MDFError("上一版本不在目标历史中", code="invalid_review_base")
    base = sha(repo, base)
    left = sha(repo, review_base) if review_base else base
    if not ancestor(repo, left, head) or not ancestor(repo, base, left):
        raise MDFError("审查基线必须是 head 祖先", code="invalid_review_base")
    if review_base and left != base and previous is None:
        raise MDFError("增量复核需要 --previous-report", code="missing_previous_review")
    rule = manifest.get("rules", {}).get("code-review")
    project = {"path": rule, "content": blob(repo, policy_ref, rule)} if rule else None
    agents = blob(repo, policy_ref, "AGENTS.md", required=False)
    protocol_path = Path(__file__).resolve().parents[3] / "references/reviewer-protocol.md"
    protocol = protocol_path.read_text(encoding="utf-8")
    rules = {"mdf": protocol, "project": project, "agents": agents,
             "modules": blob(repo, policy_ref, ".mdf/modules.yaml", required=False)}
    scope_config, scope_raw = source_modules(repo, head)
    rules["scope"] = {"modules": scope_raw}
    review_paths, review_diff = review_changes(repo, left, head, scope_config)
    target_paths, target_diff = review_changes(repo, merge_base, policy_ref, scope_config)
    artifacts, incomplete = {}, []
    for name in ("objectives.md", "code-review.md", "verification-report.json", "fact-audit.md", "CHANGE.md"):
        raw = blob(repo, artifact_ref, root + "/" + name, required=False)
        if raw is None:
            incomplete.append(root + "/" + name)
        else:
            artifacts[root + "/" + name] = raw
    objectives = artifacts.get(root + "/objectives.md", "")
    if not re.search(r"(?m)^- \[x\] code-review\s*$", objectives):
        incomplete.append("本地 code-review 尚未完成")
    try:
        verification = json.loads(artifacts.get(root + "/verification-report.json", "{}"))
        if not isinstance(verification, dict) or verification.get("all_passed") is not True:
            incomplete.append("verification-report.json 未声称通过")
    except ValueError:
        incomplete.append("verification-report.json 无效")
    if previous is not None:
        if previous.get("policy_ref") != policy_ref:
            raise MDFError("目标已变化；需要完整首轮审查", code="invalid_previous_review")
        if (previous.get("review_head") != left or previous.get("source") != source
                or previous.get("delivery_base") != base):
            raise MDFError("上轮报告与增量左端点不符", code="invalid_previous_review")
        if (previous.get("rules_sha256") != fingerprint(rules) or previous.get("incomplete")
                or previous.get("decision") not in {"pass", "changes_requested"}
                or len(previous.get("reviewers", [])) != roster["reviewers"]
                or any(r.get("incomplete") for r in previous.get("reviewers", []))):
            raise MDFError("上轮规则已变化或报告不完整；需要完整首轮审查", code="invalid_previous_review")
    result = {"schema_version": 3, "source": source, "kind": details["kind"],
              "delivery_base": base, "review_base": left, "review_head": head, "policy_ref": policy_ref,
              "scope": "delivery", "merge_base": merge_base,
              "target_paths": target_paths,
              "target_diff": target_diff,
              "round": "incremental" if previous is not None else "initial", "roster": roster,
              "rules": rules, "rules_sha256": fingerprint(rules), "artifacts": artifacts,
              "paths": review_paths,
              "diff": review_diff,
              "incomplete": incomplete, "previous_report": previous,
              "target": "master" if details["kind"] in {"release", "hotfix"} else "develop"}
    if publication:
        result["publication"] = publication
    result["context_sha256"] = fingerprint(result)
    return result


def command_context(args):
    repo = repo_path(args.repo)
    require_git_root(repo)
    previous = read_json(Path(args.previous_report)) if args.previous_report else None
    emit({"ok": True, "result": context(repo, args.source, args.head, args.policy_ref, args.review_base, previous,
                                       against=args.against)})
