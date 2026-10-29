"""校验外部复核报告；格式完整不等于 finding 语义成立。"""
import json
from pathlib import Path

from mdf_core.foundation.errors import MDFError, emit
from mdf_core.lifecycle.delivery_state import read_json
from mdf_core.reviewing.context import fingerprint

DECISIONS = {"pass", "changes_requested", "needs-review", "error"}


def require(condition, message):
    if not condition:
        raise MDFError(message, code="invalid_review_report")


def validate(context, report):
    from mdf_core.reviewing.schema import check
    if isinstance(context, dict) and context.get("mode") == "against":
        from mdf_core.reviewing.standalone import validate_against_report
        return validate_against_report(context, report)
    schema = Path(__file__).resolve().parents[3] / 'assets/templates/ci-review-report.schema.json'
    check(report, json.loads(schema.read_text(encoding='utf-8')))
    required = {"source", "delivery_base", "review_base", "review_head", "policy_ref", "rules_sha256", "context_sha256",
                "roster", "paths", "incomplete", "round"}
    require(isinstance(context, dict) and required <= set(context), "context 缺少必需字段")
    require(isinstance(context["paths"], list) and all(isinstance(p, str) for p in context["paths"]), "context paths 无效")
    require(isinstance(context["incomplete"], list) and isinstance(context["roster"], dict), "context 结构无效")
    require(type(context["roster"].get("reviewers")) is int and context["roster"]["reviewers"] > 0, "context 人数无效")
    require(context["roster"].get("review_strategy") in {"replicate", "partition"}, "context 策略无效")
    original = {key: value for key, value in context.items() if key != "context_sha256"}
    require(context.get("context_sha256") == fingerprint(original), "context 内容与指纹不符")
    require(context["round"] == ("incremental" if context.get("previous_report") is not None else "initial"), "上轮报告与 round 不符")
    for name in ("source", "delivery_base", "review_base", "review_head", "policy_ref", "rules_sha256", "context_sha256"):
        require(report.get(name) == context[name], f"报告 {name} 与本轮不符")
    require(report.get("schema_version") == 3, "报告 schema_version 必须为 3")
    decision = report.get("decision")
    require(decision in DECISIONS, "报告 decision 无效")
    require(isinstance(report.get("incomplete"), list), "报告需要 incomplete")
    reviewers = report.get("reviewers")
    require(isinstance(reviewers, list), "报告需要 reviewers")
    require(len(reviewers) == context["roster"]["reviewers"], "独立报告份数与冻结 roster 不符")
    identities, covered, findings, reopened = set(), set(), {}, set()
    previous = context.get("previous_report") or {}
    old_findings = {f["id"]: f for r in previous.get("reviewers", []) for f in r.get("findings", [])}
    for reviewer in reviewers:
        require(isinstance(reviewer, dict), "reviewer 必须为 object")
        name = reviewer.get("id")
        require(isinstance(name, str) and name.strip() and name not in identities, "reviewer 身份缺失或重复")
        identities.add(name)
        require(reviewer.get("rules_sha256") == context["rules_sha256"], "reviewer rule 指纹不符")
        require(isinstance(reviewer.get("incomplete"), list), "reviewer 需要 incomplete")
        require(isinstance(reviewer.get("paths"), list), "reviewer 需要 paths 覆盖声明")
        own = set(reviewer["paths"])
        require(own <= set(context["paths"]), "reviewer 范围超出本轮")
        if context["roster"]["review_strategy"] == "replicate" or len(reviewers) == 1:
            require(own == set(context["paths"]), "replicate 或单人必须覆盖本轮全部路径")
        covered |= own
        require(isinstance(reviewer.get("findings"), list), "reviewer 需要 findings")
        for item in reviewer["findings"]:
            require(isinstance(item, dict), "finding 必须为 object")
            identifier = item.get("id")
            require(isinstance(identifier, str) and identifier and identifier not in findings, "finding id 缺失或重复")
            for key in ("path", "trigger", "impact", "evidence"):
                require(isinstance(item.get(key), str) and item[key].strip(), f"finding 需要 {key}")
            require(type(item.get("line")) is int and item["line"] > 0, "finding line 无效")
            require(type(item.get("priority")) is int and 0 <= item["priority"] <= 3, "finding priority 无效")
            findings[identifier] = item
        if context["round"] == "incremental":
            require(isinstance(reviewer.get("previous_findings"), list), "增量需要上轮问题复核表")
            rows = reviewer["previous_findings"]
            require(len(rows) == len(old_findings) and {f["id"] for f in rows} == set(old_findings), "上轮问题复核表不完整")
            reopened.update(f["id"] for f in rows if f["state"] == "reopened")
    require(covered == set(context["paths"]), "本轮路径覆盖不完整")
    adjudications = report.get("adjudications")
    require(isinstance(adjudications, list), "需要 CI owner adjudications")
    adjudicated = set()
    # reopened 缺少完整 finding 时只能交接；保留原 ID 和原级别后才能进入正常裁定。
    pending = bool(reopened - set(findings))
    for identifier in reopened & set(findings):
        require(findings[identifier]["priority"] == old_findings[identifier]["priority"], "重新打开的旧问题不得静默改级")
    blocking = False
    for item in adjudications:
        require(isinstance(item, dict), "裁定必须为 object")
        identifier = item.get("id")
        require(identifier in findings and identifier not in adjudicated, "裁定引用不存在或重复的 finding")
        require(item.get("decision") in {"accepted", "rejected", "needs-review"}, "finding 裁定无效")
        require(isinstance(item.get("reason"), str) and item["reason"].strip(), "裁定需要理由")
        require(isinstance(item.get("evidence"), list) and item["evidence"], "裁定需要证据指针")
        require(type(item.get("needs_reproduction")) is bool, "裁定需明确是否等待复现")
        adjudicated.add(identifier)
        pending |= item["decision"] == "needs-review" or item["needs_reproduction"]
        blocking |= item["decision"] == "accepted" and findings[identifier]["priority"] <= 1
    require(adjudicated == set(findings), "仍有未裁定 finding")
    incomplete = context["incomplete"] or report["incomplete"] or any(r["incomplete"] for r in reviewers)
    if pending or incomplete:
        require(decision in {"needs-review", "error"}, "未完成或待复现时不能批准或拒绝")
    elif blocking:
        require(decision == "changes_requested", "已采纳阻断项不能批准")
    elif decision == "changes_requested":
        require(any(a["decision"] == "accepted" for a in adjudications), "request changes 需要已采纳问题")
    return {"valid": True, "decision": decision, "review_head": context["review_head"]}


def command_report_check(args):
    context = read_json(Path(args.context_file))
    report = read_json(Path(args.report_file))
    if report.get("type") == "result":
        require(not report.get("is_error") and report.get("subtype") == "success", "Cursor CLI 执行失败")
        try:
            report = json.loads(report["result"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MDFError("Cursor result 不是完整 JSON 报告", code="invalid_review_report") from exc
    require(isinstance(report, dict), "报告必须是 JSON object")
    emit({"ok": True, "result": validate(context, report), "report": report})
