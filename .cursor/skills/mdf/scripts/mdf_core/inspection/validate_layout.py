from pathlib import Path

from mdf_core.foundation.constants import RETIRED_DOC_DIRS, RETIRED_TESTING_HANDBOOK, TESTING_INDEX
from mdf_core.foundation.errors import Finding, add_finding
from mdf_core.foundation.paths import path_stays_in_repo


def validate_layout(repo: Path, findings: list[Finding]) -> None:
    """docs 布局必须符合当前契约；不属于当前布局的目录由 migrate 收敛。"""
    for raw in RETIRED_DOC_DIRS:
        path = repo / raw
        if path.is_dir() and not path.is_symlink() and path_stays_in_repo(
            repo, path
        ):
            add_finding(
                findings,
                "layout.migrate",
                f"{raw} 不属于当前文档布局；运行 $mdf migrate 收敛",
                raw,
            )
    handbook = repo / RETIRED_TESTING_HANDBOOK
    if (
        handbook.is_file()
        and not handbook.is_symlink()
        and path_stays_in_repo(repo, handbook)
    ):
        add_finding(
            findings,
            "layout.migrate",
            f"{RETIRED_TESTING_HANDBOOK} 不属于当前文档布局；"
            "迁入 docs/system/testing/ 后运行 $mdf migrate",
            RETIRED_TESTING_HANDBOOK,
        )
    _validate_testing_facet(repo, findings)


def _validate_testing_facet(repo: Path, findings: list[Finding]) -> None:
    index = repo / TESTING_INDEX
    if (
        not index.is_file()
        or index.is_symlink()
        or not path_stays_in_repo(repo, index)
    ):
        add_finding(
            findings,
            "layout.testing",
            f"缺少 {TESTING_INDEX}；init 会写入，migrate 须补齐",
            TESTING_INDEX,
        )
        return
    siblings = [
        path
        for path in index.parent.glob("*.md")
        if path.is_file()
        and not path.is_symlink()
        and path.name != "index.md"
        and path_stays_in_repo(repo, path)
    ]
    if not siblings:
        add_finding(
            findings,
            "layout.testing",
            f"{TESTING_INDEX} 须路由到至少一份主题叶",
            TESTING_INDEX,
        )
