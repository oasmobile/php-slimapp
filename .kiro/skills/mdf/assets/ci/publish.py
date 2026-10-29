"""项目侧发布示例；默认只发布 review，approve/merge 必须显式开启。"""
import argparse
import json
import sys
from pathlib import Path

MDF = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MDF / 'scripts'))

from mdf_core.integrations.forge import Forge, origin  # noqa: E402
from mdf_core.reviewing.context import context  # noqa: E402
from mdf_core.reviewing.report import validate  # noqa: E402
from mdf_core.workspace.merge_policy import git, sha  # noqa: E402


def all_rows(forge, endpoint):
    rows, page = [], 1
    while True:
        batch = forge.api(endpoint + f'?per_page=100&page={page}')
        if not isinstance(batch, list):
            raise ValueError('平台列表响应无效')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1


def publish(args):
    repo = Path(args.repo).resolve()
    ctx = json.loads(Path(args.context_file).read_text())
    report = json.loads(Path(args.report_file).read_text())
    validate(ctx, report)
    if ctx.get('mode') == 'against':
        raise ValueError('独立 against 报告由接入项目发布；此示例仅支持交付模式')
    forge = Forge(repo, origin(repo, args.provider))
    pull = forge.get(args.number)
    if (pull['state'] != 'open' or pull['head'] != ctx['review_head']
            or pull['source'] != ctx['source'] or pull['target'] != ctx['target']):
        raise ValueError('平台 head/source/target/state 已变化，重新审查')
    git(repo, 'fetch', 'origin', '--prune')
    policy = sha(repo, 'refs/remotes/origin/' + pull['target'])
    current = context(repo, ctx['source'], ctx['review_head'], policy, ctx['review_base'], ctx.get('previous_report'))
    if current['rules_sha256'] != ctx['rules_sha256'] or policy != ctx['policy_ref']:
        raise ValueError('目标分支或适用规则已变化，重新审查和验证')
    marker = '<!-- MDF review ' + ctx['context_sha256'] + ' -->'
    body = marker + '\nMDF CI review: ' + report['decision'] + '\n'
    decisions = {item['id']: item for item in report['adjudications']}
    for reviewer in report['reviewers']:
        for item in reviewer['findings']:
            verdict = decisions[item['id']]
            body += (f"\n- [{verdict['decision']}] P{item['priority']} {item['path']}:{item['line']}："
                     f"{item['trigger']}；{item['impact']}；{item['evidence']}。裁定：{verdict['reason']}")
        for item in reviewer['previous_findings']:
            if item['state'] == 'reopened':
                body += f"\n- 旧问题重新打开 {item['id']}：{item['evidence']}"
    for missing in ctx['incomplete'] + report['incomplete']:
        body += '\n- 待完成：' + missing
    if forge.github:
        existing = all_rows(forge, f'{forge.endpoint}/{args.number}/reviews')
        event = ('APPROVE' if args.approve and report['decision'] == 'pass' else
                 'REQUEST_CHANGES' if report['decision'] == 'changes_requested' else 'COMMENT')
        expected_state = {'COMMENT': 'COMMENTED', 'APPROVE': 'APPROVED', 'REQUEST_CHANGES': 'CHANGES_REQUESTED'}[event]
        if not any(marker in item.get('body', '') and item.get('state') == expected_state for item in existing):
            forge.api(f'{forge.endpoint}/{args.number}/reviews', 'POST',
                      {'commit_id': ctx['review_head'], 'body': body, 'event': event})
    else:
        notes = all_rows(forge, f'{forge.endpoint}/{args.number}/notes')
        if not any(marker in item.get('body', '') for item in notes):
            forge.api(f'{forge.endpoint}/{args.number}/notes', 'POST', {'body': body})
        if args.approve and report['decision'] == 'pass':
            forge.api(f'{forge.endpoint}/{args.number}/approve', 'POST', {'sha': ctx['review_head']})
        elif report['decision'] == 'changes_requested':
            forge.api(f'{forge.endpoint}/{args.number}/unapprove', 'POST', {})
    if args.merge:
        if not args.approve or report['decision'] != 'pass' or not args.checks_passed:
            raise ValueError('merge 需要 pass、显式 approve 和项目已核实的 checks-passed')
        endpoint = f'{forge.endpoint}/{args.number}/merge'
        body = ({'sha': ctx['review_head'], 'merge_method': 'merge'} if forge.github else
                {'sha': ctx['review_head'], 'squash': False, 'auto_merge': True})
        forge.api(endpoint, 'PUT', body)
    return {'decision': report['decision'], 'pull_request': pull['url']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'context-file', 'report-file'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--number', type=int, required=True)
    parser.add_argument('--provider', choices=('github', 'gitlab'), required=True)
    for name in ('approve', 'merge', 'checks-passed'):
        parser.add_argument('--' + name, action='store_true')
    try:
        print(json.dumps(publish(parser.parse_args()), ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
