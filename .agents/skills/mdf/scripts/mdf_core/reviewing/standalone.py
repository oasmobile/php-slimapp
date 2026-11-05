"""独立 against 审查：历史版本与当前工作区的只读审阅。"""
import json
from pathlib import Path

from tempfile import TemporaryDirectory

from mdf_core.execution.modules import parse_modules
from mdf_core.foundation.yamlutil import parse_yaml
from mdf_core.reviewing.scope import review_document, selected_diff
from mdf_core.reviewing.worktree import working_snapshot
from mdf_core.foundation.errors import MDFError
from mdf_core.reviewing.context import fingerprint
from mdf_core.reviewing.policy import current_policy
from mdf_core.workspace.project_rules import load_project_rule
from mdf_core.reviewing.schema import check
from mdf_core.workspace.merge_policy import git, sha


def against_context(repo, against):
    base = sha(repo, against)
    with TemporaryDirectory(prefix='mdf-review-') as folder:
        work = Path(folder).resolve() / 'worktree'
        files = working_snapshot(repo, work)
        local = current_policy(work)
        config = parse_modules(parse_yaml(local['modules']))
        protocol = Path(__file__).resolve().parents[3] / 'references/reviewer-protocol.md'
        rules = {**local, 'mdf': protocol.read_text(encoding='utf-8'),
                 'project': load_project_rule(work, local['manifest'], 'code-review')}
        changed = git(work, 'diff', '--no-renames', '--name-only', '-z', base, '--').stdout.split('\0')
        selected = [p for p in changed if p and (config.owns(p) or review_document(p)) and not config.is_ignored(p)]
        result = {'schema_version': 3, 'mode': 'against', 'scope': 'worktree',
                  'against': base, 'worktree_sha256': fingerprint(files), 'paths': selected,
                  'diff': selected_diff(work, base, None, selected),
                  'rules': rules, 'rules_sha256': fingerprint(rules), 'incomplete': []}
    result['context_sha256'] = fingerprint(result)
    return result


def validate_against_report(context, report):
    from mdf_core.reviewing.report import require
    template = Path(__file__).resolve().parents[3] / 'assets/templates/against-review-report.schema.json'
    check(report, json.loads(template.read_text(encoding='utf-8')))
    required = {'schema_version', 'mode', 'scope', 'against', 'worktree_sha256',
                'paths', 'rules', 'rules_sha256', 'context_sha256', 'incomplete'}
    require(required <= set(context), 'context 缺少必需字段')
    require(not {'source', 'delivery_base', 'roster', 'artifacts'} & set(context), '独立 context 不接受交付字段')
    require(context['schema_version'] == 3 and context['scope'] == 'worktree', 'context 模式无效')
    require(isinstance(context['paths'], list) and all(isinstance(p, str) for p in context['paths']), 'context paths 无效')
    require(isinstance(context['incomplete'], list), 'context incomplete 无效')
    original = {k: v for k, v in context.items() if k != 'context_sha256'}
    require(context['context_sha256'] == fingerprint(original), 'context 内容与指纹不符')
    require(context['rules_sha256'] == fingerprint(context['rules']), 'context 规则与指纹不符')
    for key in ('mode', 'against', 'worktree_sha256', 'rules_sha256', 'context_sha256'):
        require(report[key] == context[key], f'报告 {key} 与本轮不符')
    require(set(report['paths']) == set(context['paths']), '报告路径覆盖不完整')
    identifiers = set()
    for finding in report['findings']:
        for key in ('id', 'path', 'trigger', 'impact', 'evidence'):
            require(bool(finding[key].strip()), f'finding 需要 {key}')
        require(finding['id'] not in identifiers, 'finding id 重复')
        identifiers.add(finding['id'])
    decision = report['decision']
    if context['incomplete'] or report['incomplete']:
        require(decision in {'needs-review', 'error'}, '未完成时不能批准或拒绝')
    elif any(f['priority'] <= 1 for f in report['findings']):
        require(decision in {'changes_requested', 'needs-review', 'error'}, '阻断项不能批准')
    if decision == 'changes_requested':
        require(bool(report['findings']), 'request changes 需要 findings')
    return {'valid': True, 'decision': decision, 'against': context['against'], 'worktree_sha256': context['worktree_sha256']}
