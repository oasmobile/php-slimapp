"""未共享线性尾段的 squash 边界与动作前检查；不决定语义分段。"""
import hashlib
import json
from pathlib import Path

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.gitutil import branch_details, current_branch, ensure_clean
from mdf_core.workspace.merge_policy import configured, git, planning_only, sha


def common_dir(repo):
    return Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip())


def receipt_path(repo, branch):
    key = hashlib.sha256(branch.encode()).hexdigest()
    return common_dir(repo) / 'mdf' / 'squash' / f'{key}.json'


def inspect(repo, branch=None, *, refresh=True):
    """仅最后一个保护边界之后的本人普通提交可改写。"""
    branch = branch or current_branch(repo)
    head = sha(repo, f'refs/heads/{branch}')
    if refresh:
        for remote in git(repo, 'remote').stdout.splitlines():
            # 显式获取所有分支，不依赖可能只覆盖一个分支的 fetch refspec。
            git(repo, 'fetch', remote, f'+refs/heads/*:refs/remotes/{remote}/*', '--tags')
    if branch == 'planning':
        target = 'refs/heads/develop'
        if (not git(repo, 'cat-file', '-e', f'{target}:.mdf/manifest.yaml', check=False).returncode
                and configured(repo, target)['mode'] == 'pr' and not planning_only(repo, target, head)):
            raise MDFError('planning 须先通过完整文档历史检查，不得用 squash 隐藏代码改动', code='pr_required')
    refs = git(repo, 'for-each-ref', '--format=%(refname)', 'refs/heads', 'refs/remotes', 'refs/tags').stdout.splitlines()
    protected = set()
    for ref in refs:
        if ref == f'refs/heads/{branch}':
            continue
        resolved = git(repo, 'rev-parse', '--verify', f'{ref}^{{commit}}', check=False)
        if resolved.returncode == 0:
            protected.add(resolved.stdout.strip())
        elif not ref.startswith('refs/tags/'):
            raise MDFError('无法解析共享引用', code='squash_boundary_unknown')
    for block in git(repo, 'worktree', 'list', '--porcelain').stdout.strip().split('\n\n'):
        rows = block.splitlines()
        if f'branch refs/heads/{branch}' not in rows:
            protected.update(row[5:] for row in rows if row.startswith('HEAD '))
    # 已准备的 PR/push 恢复端点也不可改写，即使远端响应尚未确认。
    finish = common_dir(repo) / 'mdf' / 'finish'
    for path in finish.rglob('*.json') if finish.exists() else []:
        try:
            record = json.loads(path.read_text())
            if record.get('source') == branch:
                protected.update(record[k] for k in ('head', 'pending_head') if record.get(k))
            back = record.get('backmerge') or {}
            if back.get('source') == branch:
                protected.update(back[k] for k in ('base', 'head') if back.get(k))
        except (ValueError, TypeError, AttributeError) as exc:
            raise MDFError('收口记录损坏，无法确定 squash 边界', code='squash_boundary_unknown') from exc
    owner = branch
    from mdf_core.lifecycle.roster import parse_role_branch
    role = parse_role_branch(branch)
    if role:
        owner = role[0]
    if branch_details(branch)['kind'] == 'adhoc' and not role and not branch.startswith('codex/backmerge/'):
        from mdf_core.lifecycle.adhoc_context import material
        from mdf_core.foundation.yamlutil import read_frontmatter
        root, ledger = material(repo, branch)
        change = root / 'CHANGE.md'
        if not ledger and change.is_file():
            metadata, _ = read_frontmatter(change)
            evidence = metadata.get('evidence')
            fixed = evidence.get('range') if isinstance(evidence, dict) else None
            if fixed is not None:
                if not isinstance(fixed, dict) or not fixed.get('source_head'):
                    raise MDFError('Change 固定范围无效', code='squash_boundary_unknown')
                protected.add(sha(repo, fixed['source_head']))
    start = git(repo, 'config', '--get', f'branch.{owner}.mdf-start-commit', check=False)
    if start.returncode == 0:
        protected.add(sha(repo, start.stdout.strip()))
    elif start.returncode != 1:
        raise MDFError('无法读取交付起点', code='squash_boundary_unknown')
    shared = set(git(repo, 'rev-list', *sorted(protected)).stdout.splitlines()) if protected else set()
    email = git(repo, 'var', 'GIT_COMMITTER_IDENT').stdout.split('<', 1)[1].split('>', 1)[0]
    commits = []
    floor = head
    for row in git(repo, 'log', '--first-parent', '--format=%H%x09%P%x09%ae%x09%ce', head).stdout.splitlines():
        commit, parents, author, committer = row.split('\t')
        floor = commit
        if commit in shared or len(parents.split()) != 1 or author != email or committer != email:
            break
        commits.append(commit)
    return {'branch': branch, 'old_tip': head, 'floor': floor,
            'commits': list(reversed(commits)), 'noop': len(commits) < 2}


def record_analysis(repo, branch, head, *, reason):
    path = receipt_path(repo, branch)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'branch': branch, 'head': head, 'reason': reason}, ensure_ascii=False) + '\n')
    temporary.replace(path)


def require_ready(repo, branch=None):
    """每次动作重新核边界；多笔尾段必须先由 Agent 分析并执行计划。"""
    from mdf_core.lifecycle.roster import parse_role_branch
    branch = branch or current_branch(repo)
    if branch != 'planning' and configured(repo)['mode'] != 'pr':
        return
    if not (branch == 'planning'
            or branch_details(branch)['supported']
            or parse_role_branch(branch)):
        return
    plan = inspect(repo, branch)
    if plan['noop']:
        return plan
    path = receipt_path(repo, plan['branch'])
    if path.exists():
        try:
            receipt = json.loads(path.read_text())
        except ValueError as exc:
            raise MDFError('squash 检查记录损坏', code='squash_required') from exc
        if receipt.get('branch') == plan['branch'] and receipt.get('head') == plan['old_tip']:
            return plan
    raise MDFError('动作前须分析未共享提交并执行 squash 计划；完成后重试',
                   code='squash_required', details=plan)


def check(repo):
    ensure_clean(repo)
    return inspect(repo)
