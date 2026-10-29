"""独立事实报告校验：固定范围、逐项覆盖、warning 处置与完成状态。"""
import json
from pathlib import Path

from mdf_core.foundation.errors import emit
from mdf_core.lifecycle.delivery_state import read_json
from mdf_core.reviewing.context import fingerprint
from mdf_core.reviewing.report import require
from mdf_core.reviewing.schema import check


def validate_fact_report(context, report):
    schema = Path(__file__).resolve().parents[3] / 'assets/templates/against-fact-audit-report.schema.json'
    check(report, json.loads(schema.read_text(encoding='utf-8')))
    require(isinstance(context, dict) and {'audit', 'rules', 'rules_sha256', 'context_sha256',
            'implementation_paths', 'document_paths', 'paths', 'incomplete'} <= context.keys(), 'context 缺少字段')
    for key in ('paths', 'implementation_paths', 'document_paths', 'incomplete'):
        require(isinstance(context[key], list) and all(isinstance(p, str) for p in context[key]),
                f'context {key} 必须为字符串列表')
    audit = context['audit']
    require(isinstance(audit, dict) and {'warnings', 'findings'} <= audit.keys(), 'context audit 缺少字段')
    for key in ('warnings', 'findings'):
        require(isinstance(audit[key], list) and all(isinstance(f, dict) for f in audit[key]),
                f'context audit.{key} 必须为 object 列表')
    require(context['context_sha256'] == fingerprint({k: v for k, v in context.items() if k != 'context_sha256'}),
            'context 内容与指纹不符')
    require(context['rules_sha256'] == fingerprint(context['rules']), '规则与指纹不符')
    for key in ('schema_version', 'mode', 'operation', 'against', 'worktree_sha256',
                'rules_sha256', 'context_sha256'):
        require(report[key] == context.get(key), f'报告 {key} 与本轮不符')
    pending = bool(context['incomplete'] or report['incomplete'])
    for key in ('paths', 'implementation_paths', 'document_paths'):
        actual, expected = report[key], context[key]
        require(len(actual) == len(set(actual)) and set(actual) <= set(expected), f'{key} 重复或超出范围')
        pending |= set(actual) != set(expected)
    warnings = context['audit']['warnings']
    seen = set()
    for row in report['warnings']:
        index = row['index']
        require(index < len(warnings) and index not in seen, 'warning 不存在或重复')
        require(bool(row['evidence'].strip()), 'warning 处置需要证据')
        pending |= row['disposition'] == 'needs-review'
        seen.add(index)
    pending |= len(seen) != len(warnings)
    ids = set()
    for finding in report['findings']:
        require(finding['id'] not in ids, 'finding id 重复')
        ids.add(finding['id'])
        for key in ('id', 'path', 'trigger', 'impact', 'evidence'):
            require(bool(finding[key].strip()), f'finding 需要 {key}')
    blocked = bool(context['audit']['findings'] or report['findings'] or
                   any(row['disposition'] == 'finding' for row in report['warnings']))
    decision = report['decision']
    if pending:
        require(decision in {'needs-review', 'error'}, '未完成复核不能通过或拒绝')
        require(bool(report['incomplete']), '未完成复核须说明缺项')
    if blocked:
        require(decision != 'pass', '存在事实或 validation finding，不能通过')
    if decision == 'changes_requested':
        require(blocked, 'changes_requested 需要 finding')
    return {'valid': True, 'decision': decision, 'against': context['against'], 'worktree_sha256': context['worktree_sha256']}


def command_fact_report_check(args):
    context = read_json(Path(args.context_file))
    report = read_json(Path(args.report_file))
    emit({'ok': True, 'result': validate_fact_report(context, report), 'report': report})
