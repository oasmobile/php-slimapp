"""交付材料定位、稳定基线与内容指纹。"""
import fnmatch
import hashlib
import json
from pathlib import Path

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import branch_details, current_branch, run, unreleased_slug
from mdf_core.foundation.paths import load_manifest, path_stays_in_repo
from mdf_core.lifecycle.roster import fingerprint_data, owner_branch, require_roster
from mdf_core.execution.verification import repo_verification

STAGES = ("design", "write-tests", "implement", "converge")


def read_objectives(path: str | None) -> str:
    from mdf_core.foundation.constants import MARKER_RE

    if not path:
        raise MDFError("需要 --objectives-file", code="missing_objectives")
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip() or MARKER_RE.search(text):
        raise MDFError("objectives 不能为空", code="missing_objectives")
    return text


def _parse_yes_no_field(text: str, name: str, missing_code: str) -> bool:
    """从 objectives 解析 `name: yes|no`（可带列表前缀）。"""
    import re
    match = re.search(
        rf"(?im)^(?:[-*]\s*)?{re.escape(name)}:\s*(yes|no|true|false)\s*$",
        text,
    )
    if not match:
        raise MDFError(
            f"objectives 必须含 {name}: yes 或 {name}: no",
            code=missing_code,
        )
    return match.group(1).lower() in {"yes", "true"}


def parse_needs_design(text: str) -> bool:
    """从 objectives 解析 `needs_design: yes|no`（可带列表前缀）。"""
    return _parse_yes_no_field(text, "needs_design", "missing_needs_design")


def parse_has_dev(text: str) -> bool:
    """从 release objectives 解析 `has_dev: yes|no`（可带列表前缀）。"""
    return _parse_yes_no_field(text, "has_dev", "missing_has_dev")


def git(repo, *args, check=True):
    return run(["git", *args], cwd=repo, check=check)


def safe(repo, path):
    path = Path(path)
    if not path.is_absolute():
        path = repo / path
    if not path_stays_in_repo(repo, path) or any(p.is_symlink() for p in (path, *path.parents)):
        raise MDFError("交付材料路径必须留在仓库内且不含符号链接", code="unsafe_path")
    return path


def read_json(path):
    try:
        value = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise MDFError(f"无法读取记录: {path.name}", code="invalid_delivery") from exc
    if not isinstance(value, dict):
        raise MDFError("记录必须为 JSON 对象", code="invalid_delivery")
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def material_root(repo, slug, *, owner=None):
    """PR 候选发布使用已归入版本目录的同一份交付材料。"""
    owner = owner if owner is not None else current_branch(repo)
    root = safe(repo, repo / "changes" / "unreleased" / slug)
    details = branch_details(owner)
    if details["kind"] in {"release", "hotfix"} and details["version"] == slug:
        from mdf_core.workspace.merge_policy import configured
        candidate = safe(repo, repo / "changes" / slug)
        record = safe(repo, candidate / "delivery.json")
        if configured(repo)["mode"] == "pr" and record.is_file():
            if (root / "delivery.json").exists():
                raise MDFError("候选发布材料存在多个目录", code="invalid_delivery")
            data = read_json(record)
            if data.get("branch") != owner or data.get("slug") != slug:
                raise MDFError("候选发布身份不匹配", code="invalid_delivery")
            return candidate
    return root


def locate(repo, slug=None, *, owner=None):
    owner = owner if owner is not None else owner_branch(current_branch(repo))
    if slug is None:
        slug = unreleased_slug(branch_details(owner))
    root = material_root(repo, slug, owner=owner)
    if not (root / "delivery.json").is_file():
        raise MDFError("交付记录缺失", code="invalid_delivery")
    data = read_json(safe(repo, root / "delivery.json"))
    if data.get("slug") != slug or data.get("branch") != owner:
        raise MDFError("交付身份不匹配", code="invalid_delivery")
    data["roster"] = require_roster(data.get("roster"))
    needs = data.get("needs_design", True)
    if not isinstance(needs, bool):
        raise MDFError("needs_design 必须为布尔值", code="invalid_delivery")
    data["needs_design"] = needs
    base = data.get("start_commit", "")
    if not isinstance(base, str) or len(base) != 40 or any(c not in "0123456789abcdef" for c in base):
        raise MDFError("起点必须为完整 commit hash", code="invalid_delivery")
    if git(repo, "merge-base", "--is-ancestor", base, "HEAD", check=False).returncode:
        raise MDFError("当前分支不包含交付起点", code="invalid_delivery")
    if owner.startswith("adhoc/"):
        from mdf_core.lifecycle.adhoc import require_identity
        require_identity(data)
    return root, data


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def matches(path, patterns):
    return any(path == item.rstrip("/") or path.startswith(item.rstrip("/") + "/")
               or fnmatch.fnmatchcase(path, item) for item in patterns)


def inventory(repo):
    raw = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
    result = {}
    for name in sorted(set(raw.split("\0")) - {""}):
        path = safe(repo, repo / name)
        if path.is_file():
            result[name] = digest([hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o111])
    return result


def fingerprints(repo, root, data, config=None, *, ref=None):
    if config is None:
        config = read_json(safe(repo, root / "design-policy.json"))
    files = inventory(repo)
    protected = config.get("protected_paths", [])
    # 预算与命令一样决定门禁结果，同属验证配置。
    commands = repo_verification(repo).config()
    facts = {name: value for name, value in files.items()
             if name == "GLOSSARY.md" or (name.endswith(".md")
                 and name.startswith(("docs/user-guide/", "docs/system/")))}
    # 文档与 Change 材料的改动不使实现审查或全绿失效；事实文档另由 facts 覆盖。
    code = {name: value for name, value in files.items()
            if name not in facts and not name.startswith(("changes/", "docs/"))
            and not ("/" not in name and name.endswith(".md"))
            and name != ".mdf/manifest.yaml"}
    tests = {name: value for name, value in code.items() if matches(name, protected)}
    implementation = {name: value for name, value in code.items() if name not in tests}
    design = {}
    names = ("objectives.md", "design.md") if data.get("needs_design", True) else ("objectives.md",)
    for name in names:
        path = safe(repo, root / name)
        if not path.is_file() or not path.read_text().strip():
            raise MDFError(f"缺少 {name}", code="missing_artifact")
        from mdf_core.foundation.constants import ALL_MARKDOWN_LINK_RE, MARKER_RE
        from mdf_core.documents.moves import rewrite_link_raw
        from mdf_core.inspection.validate_links import canonical_local_link, split_link_target
        text = (git(repo, "show", f"{ref}:{path.relative_to(repo)}").stdout
                if ref else path.read_text())
        if name == "objectives.md":
            import re
            text = re.sub(r"(?m)^([-*]\s+)\[[ xX]\]", r"\1[ ]", text)
        if MARKER_RE.search(text):
            raise MDFError("设计材料仍含模板占位内容", code="missing_artifact")
        def normalize(match):
            raw = match.group(1)
            target = split_link_target(raw)
            canonical = canonical_local_link(repo, path, target, root)
            if canonical is None:
                return match.group(0)
            # 只改 href。str.replace 会把链接文字里的同一子串一并改掉。
            full = match.group(0)
            start = match.start(1) - match.start(0)
            end = match.end(1) - match.start(0)
            return full[:start] + rewrite_link_raw(raw, canonical) + full[end:]
        design[name] = hashlib.sha256(ALL_MARKDOWN_LINK_RE.sub(normalize, text).encode()).hexdigest()
    return {"design": digest([design, fingerprint_data(data), config]),
            "tests": digest([tests, commands]),
            "implementation": digest(implementation), "code": digest([code, commands]),
            "facts": digest(facts)}


def design_on_ref(repo, root, ref):
    """只从固定 Git 提交读取共同设计，不把阶段勾选纳入 fingerprint。"""
    def record(name):
        raw = git(repo, "show", f"{ref}:{(root / name).relative_to(repo)}").stdout
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise MDFError("固定设计提交的配置无法解析", code="invalid_delivery") from exc
    data = record("delivery.json")
    policy = record("design-policy.json")
    return fingerprints(repo, root, data, policy, ref=ref)["design"]


def gate(repo, root, stage):
    return read_json(safe(repo, root / "gates" / f"{stage}.json"))


def committed_design(repo, root, data):
    """主链只核设计配置与提交，不读取阶段 Gate。"""
    if not data.get("needs_design", True):
        return fingerprints(repo, root, data, {})
    from mdf_core.lifecycle.delivery import policy_input
    policy = policy_input(safe(repo, root / "design-policy.json"))
    current = fingerprints(repo, root, data, policy)
    rels = [str((root / name).relative_to(repo))
            for name in ("objectives.md", "design.md", "delivery.json", "design-policy.json")]
    if git(repo, "ls-files", "--error-unmatch", *rels, check=False).returncode:
        raise MDFError("设计基线必须提交", code="uncommitted_design")
    if git(repo, "diff", "HEAD", "--", *rels).stdout:
        raise MDFError("设计基线必须提交", code="uncommitted_design")
    return current


def require_design(repo, root, data):
    """显式辅助 record/check 可核对其设计快照；主链不使用该检查。"""
    if data.get("needs_design", True) and (root / "gates/design.json").is_file():
        policy = read_json(safe(repo, root / "design-policy.json"))
        current = fingerprints(repo, root, data, policy)
        record = gate(repo, root, "design")
        if record.get("fingerprints", {}).get("design") != current["design"]:
            raise MDFError("设计基线已变化，需用户确认后原地重新记录", code="stale_gate")
    return committed_design(repo, root, data)


def require_finish(repo, root, data):
    """close-out 的 CLI 侧：定位交付材料；不读 converge 等进度 gate。"""
    for name in ("objectives.md", "delivery.json"):
        path = safe(repo, root / name)
        if not path.is_file():
            raise MDFError(f"缺少交付材料: {name}", code="missing_delivery")
    if data.get("needs_design", True):
        if not safe(repo, root / "design.md").is_file():
            raise MDFError("缺少 design.md", code="missing_design")
    policy = {"protected_paths": [], "suites": []}
    design_gate = root / "gates" / "design.json"
    if design_gate.is_file():
        try:
            policy = read_json(safe(repo, design_gate)).get("policy") or policy
        except MDFError:
            pass
    return fingerprints(repo, root, data, policy)
