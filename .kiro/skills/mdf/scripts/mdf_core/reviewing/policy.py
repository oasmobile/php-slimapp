"""从执行审阅的仓库工作区读取当前项目 policy，不切换 Git 版本。"""
from mdf_core.execution.modules import load_modules
from mdf_core.foundation.errors import MDFError
from mdf_core.foundation.paths import load_manifest, path_stays_in_repo


def current_policy(repo):
    manifest = load_manifest(repo)
    load_modules(repo)
    agents = repo / 'AGENTS.md'
    if agents.is_symlink() or not path_stays_in_repo(repo, agents):
        raise MDFError('AGENTS.md 必须为仓库内普通文件', code='invalid_review_context')
    return {'manifest': manifest,
            'modules': (repo / '.mdf/modules.yaml').read_text(encoding='utf-8'),
            'agents': agents.read_text(encoding='utf-8') if agents.is_file() else None}
