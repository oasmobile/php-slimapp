"""固定 source 的 module 范围与按路径提取的审查 diff。"""
from mdf_core.execution.modules import parse_modules
from mdf_core.foundation.yamlutil import parse_yaml
from pathlib import PurePosixPath
from mdf_core.workspace.merge_policy import git, paths


def source_modules(repo, head):
    from mdf_core.reviewing.context import blob
    raw = blob(repo, head, '.mdf/modules.yaml')
    return parse_modules(parse_yaml(raw)), raw


def review_document(path):
    suffix = PurePosixPath(path).suffix
    return (suffix in {'.md', '.html'} and ('/' not in path or path.startswith(('docs/', 'changes/')))
            or suffix == '.json' and path.startswith('changes/'))


def selected_diff(repo, base, head, selected):
    return git(repo, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames', base, *([head] if head else []),
               '--', *(':(literal)' + p for p in selected)).stdout if selected else ''


def review_changes(repo, base, head, config):
    selected = [p for p in paths(repo, base, head)
                if (config.owns(p) or review_document(p)) and not config.is_ignored(p)]
    return selected, selected_diff(repo, base, head, selected)
