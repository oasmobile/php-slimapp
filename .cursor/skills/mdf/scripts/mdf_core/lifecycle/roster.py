"""交付 roster：人数、并行策略、角色分支名。"""
import json
import re

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import branch_details, run

NAMED_ROSTERS = {
    "solo": {
        "qa": 0, "dev": 0, "reviewers": 1,
        "qa_strategy": "best-of-n", "dev_strategy": "best-of-n",
        "review_strategy": "replicate",
    },
    "min-tdd": {
        "qa": 1, "dev": 1, "reviewers": 2,
        "qa_strategy": "best-of-n", "dev_strategy": "best-of-n",
        "review_strategy": "replicate",
    },
    "competing-pair": {
        "qa": 2, "dev": 2, "reviewers": 3,
        "qa_strategy": "best-of-n", "dev_strategy": "best-of-n",
        "review_strategy": "replicate",
    },
    "coop-pair": {
        "qa": 2, "dev": 2, "reviewers": 3,
        "qa_strategy": "partition", "dev_strategy": "partition",
        "review_strategy": "replicate",
    },
}

KIND_ROSTER = {
    "feature": "min-tdd",
    "bugfix": "solo",
    "release": "solo",
    "hotfix": "solo",
    "adhoc": "solo",
}
# 未点名 roster 时按 kind 覆盖默认组合；release 审查面最大，默认 3 人分片审查。
KIND_DEFAULTS = {
    "release": {"reviewers": 3, "review_strategy": "partition"},
}

QA_DEV_STRATEGIES = ("best-of-n", "partition")
REVIEW_STRATEGIES = ("replicate", "partition")
COUNT_KEYS = ("qa", "dev", "reviewers")
STRATEGY_KEYS = ("qa_strategy", "dev_strategy", "review_strategy")
OPTIONAL_KEYS = ("models",)
MODEL_INTENTS = ("write-tests", "implement", "code-review")
MODEL_ARGUMENTS = (
    ("write-tests", "--write-tests-model"),
    ("implement", "--implement-model"),
    ("code-review", "--code-review-model"),
)
FINGERPRINT_KEYS = (*COUNT_KEYS, "qa_strategy", "dev_strategy")

_ROLE = re.compile(
    r"^(?P<role>qa|dev)(?:/(?P<index>[1-9]\d*))?/"
    r"(?P<owner>(?:feature|bugfix|release|hotfix)/.+)$"
)


def _counts(qa, dev, reviewers, *, coerce):
    for name, value in (("qa", qa), ("dev", dev), ("reviewers", reviewers)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise MDFError(f"roster.{name} 必须是整数", code="invalid_roster")
    if qa < 0 or dev < 0:
        raise MDFError("roster.qa 与 roster.dev 不能为负", code="invalid_roster")
    if reviewers < 1:
        raise MDFError("roster.reviewers 至少为 1", code="invalid_roster")
    if (qa == 0) != (dev == 0):
        if not coerce:
            raise MDFError("qa 与 dev 只能同时为 0 或都 ≥1",
                           code="invalid_roster")
        qa = qa or 1
        dev = dev or 1
    return {"dev": dev, "qa": qa, "reviewers": reviewers}


def _choice(name, value, allowed, default):
    if value is None:
        return default
    if value not in allowed:
        raise MDFError(
            f"roster.{name} 必须是 {' 或 '.join(allowed)}",
            code="invalid_roster",
        )
    return value


def _model_value(value):
    if not isinstance(value, str) or not value.strip():
        raise MDFError("roster.models 的取值必须是非空字符串",
                       code="invalid_roster")
    return value.strip()


def _models(value):
    if not isinstance(value, dict) or not value:
        raise MDFError("roster.models 必须按 intent 给出非空对象",
                       code="invalid_roster")
    extra = set(value) - set(MODEL_INTENTS)
    if extra:
        raise MDFError(
            "roster.models 只接受 write-tests、implement、code-review",
            code="invalid_roster",
        )
    return {key: _model_value(value[key])
            for key in MODEL_INTENTS if key in value}


def models_from_args(args):
    body = {}
    for intent, flag in MODEL_ARGUMENTS:
        value = getattr(args, flag.lstrip("-").replace("-", "_"), None)
        if value is not None:
            body[intent] = value
    return _models(body) if body else None


def _strategies(qa_strategy, dev_strategy, review_strategy, models=None):
    body = {
        "qa_strategy": _choice(
            "qa_strategy", qa_strategy, QA_DEV_STRATEGIES, "best-of-n",
        ),
        "dev_strategy": _choice(
            "dev_strategy", dev_strategy, QA_DEV_STRATEGIES, "best-of-n",
        ),
        "review_strategy": _choice(
            "review_strategy", review_strategy, REVIEW_STRATEGIES, "replicate",
        ),
    }
    if models is not None:
        body["models"] = _models(models)
    return body


def named_roster(name):
    if name not in NAMED_ROSTERS:
        raise MDFError(
            f"roster 名必须是 {' / '.join(NAMED_ROSTERS)}",
            code="invalid_roster",
        )
    return dict(NAMED_ROSTERS[name])


def freeze_roster(kind, qa=None, dev=None, reviewers=None, *,
                  named=None, qa_strategy=None, dev_strategy=None,
                  review_strategy=None, models=None):
    if kind not in KIND_ROSTER:
        raise MDFError("未知交付 kind", code="unsupported_branch")
    base = named_roster(KIND_ROSTER[kind] if named is None else named)
    if named is None:
        base.update(KIND_DEFAULTS.get(kind, {}))
    qa = base["qa"] if qa is None else qa
    dev = base["dev"] if dev is None else dev
    reviewers = base["reviewers"] if reviewers is None else reviewers
    qa_strategy = base["qa_strategy"] if qa_strategy is None else qa_strategy
    dev_strategy = base["dev_strategy"] if dev_strategy is None else dev_strategy
    review_strategy = (
        base["review_strategy"] if review_strategy is None else review_strategy
    )
    return {
        **_counts(qa, dev, reviewers, coerce=True),
        **_strategies(qa_strategy, dev_strategy, review_strategy, models),
    }


def require_roster(value):
    allowed = set(COUNT_KEYS) | set(STRATEGY_KEYS) | set(OPTIONAL_KEYS)
    if not isinstance(value, dict) or set(value) - allowed:
        raise MDFError("roster 必须含 qa、dev、reviewers 与策略字段",
                       code="invalid_roster")
    missing = (set(COUNT_KEYS) | set(STRATEGY_KEYS)) - set(value)
    if missing:
        raise MDFError("roster 必须含 qa、dev、reviewers 与策略字段",
                       code="invalid_roster")
    return {
        **_counts(value["qa"], value["dev"], value["reviewers"], coerce=False),
        **_strategies(
            value["qa_strategy"], value["dev_strategy"],
            value["review_strategy"], value.get("models"),
        ),
    }


def fingerprint_roster(roster):
    roster = require_roster(roster)
    return {key: roster[key] for key in FINGERPRINT_KEYS}


def fingerprint_data(data):
    payload = dict(data)
    payload["roster"] = fingerprint_roster(data["roster"])
    return payload


def add_strategy_arguments(parser):
    parser.add_argument("--qa-strategy", choices=QA_DEV_STRATEGIES)
    parser.add_argument("--dev-strategy", choices=QA_DEV_STRATEGIES)
    parser.add_argument("--review-strategy", choices=REVIEW_STRATEGIES)
    for _, flag in MODEL_ARGUMENTS:
        parser.add_argument(flag)


def add_named_roster_argument(parser):
    parser.add_argument("--roster", choices=tuple(NAMED_ROSTERS))


def apply_roster_patch(current, patch, *, locked_qa_dev):
    current = require_roster(current)
    if not patch:
        raise MDFError("未指定要更新的 roster 字段", code="invalid_roster")
    extra = set(patch) - set(STRATEGY_KEYS) - set(OPTIONAL_KEYS)
    if extra:
        raise MDFError("roster 更新只接受 strategy 与 models",
                       code="invalid_roster")
    if locked_qa_dev:
        for key in ("qa_strategy", "dev_strategy"):
            if key in patch and patch[key] != current[key]:
                raise MDFError("design 后不能改 qa/dev strategy",
                               code="roster_locked")
    merged = dict(current)
    for key, value in patch.items():
        if key == "models":
            body = dict(current.get("models") or {})
            body.update(_models(value))
            merged["models"] = body
        else:
            merged[key] = value
    return require_roster(merged)


def role_branch(role, owner, index):
    if role not in {"qa", "dev"} or index < 1:
        raise MDFError("非法角色分支", code="invalid_roster")
    if index == 1:
        return f"{role}/{owner}"
    return f"{role}/{index}/{owner}"


def role_branches(owner, roster):
    roster = require_roster(roster)
    names = []
    for role in ("qa", "dev"):
        for index in range(1, roster[role] + 1):
            names.append(role_branch(role, owner, index))
    return names


def start_branches(owner, roster):
    return [owner, *role_branches(owner, roster)]


def parse_role_branch(branch):
    match = _ROLE.fullmatch(branch)
    if match is None or match.group("index") == "1":
        return None
    index = 1 if match.group("index") is None else int(match.group("index"))
    return match.group("owner"), match.group("role"), index


def owner_branch(branch):
    parsed = parse_role_branch(branch)
    if parsed is not None:
        return parsed[0]
    if branch_details(branch)["supported"]:
        return branch
    raise MDFError("阶段操作需要交付或 qa/dev 角色分支",
                   code="unsupported_branch")


def roster_config_key(owner):
    return f"branch.{owner}.mdf-roster"


def write_roster_config(repo, owner, roster):
    payload = json.dumps(require_roster(roster), ensure_ascii=False,
                         sort_keys=True)
    run(["git", "config", "--local", roster_config_key(owner), payload],
        cwd=repo)


def read_roster_config(repo, owner):
    result = run(
        ["git", "config", "--local", "--get", roster_config_key(owner)],
        cwd=repo, check=False,
    )
    if result.returncode:
        raise MDFError("roster 未冻结", code="invalid_roster")
    try:
        value = json.loads(result.stdout.strip())
    except ValueError as exc:
        raise MDFError("roster 配置损坏", code="invalid_roster") from exc
    return require_roster(value)


def resolve_roster(repo, owner, kind):
    try:
        return read_roster_config(repo, owner)
    except MDFError:
        return freeze_roster(kind)


def winner_branch(role, owner, roster, specified):
    roster = require_roster(roster)
    count = roster[role]
    expected = [role_branch(role, owner, index)
                for index in range(1, count + 1)]
    if count == 0:
        if specified:
            raise MDFError(f"{role} roster 为 0，不要传 winner",
                           code="unexpected_winner")
        return None
    if specified is None:
        if count == 1:
            return expected[0]
        raise MDFError(f"{role} 人数 ≥2 时必须指定 winner 分支",
                       code="missing_winner")
    if specified not in expected:
        raise MDFError(f"{role} winner 不属于本次 roster",
                       code="invalid_winner")
    return specified


def merge_branches(role, owner, roster, specified):
    roster = require_roster(roster)
    if roster[f"{role}_strategy"] == "partition":
        if specified:
            raise MDFError(f"{role} 为 partition 时不要传 winner",
                           code="unexpected_winner")
        return [role_branch(role, owner, index)
                for index in range(1, roster[role] + 1)]
    winner = winner_branch(role, owner, roster, specified)
    return [] if winner is None else [winner]
