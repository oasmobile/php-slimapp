from mdf_core.foundation.errors import MDFError


def bump_kind(
    previous: tuple[int, int, int], candidate: tuple[int, int, int]
) -> str:
    if candidate <= previous:
        raise MDFError(
            "Candidate version must be greater than previous",
            code="not_increasing",
        )
    # 0.x 仍在初始开发：第二位是 major，第三位是 minor。升到 1.0.0 仍按第一位记 major。
    if previous[0] == 0 and candidate[0] == 0:
        if candidate[1] != previous[1]:
            return "major"
        return "minor"
    if candidate[0] != previous[0]:
        return "major"
    if candidate[1] != previous[1]:
        return "minor"
    return "patch"


def required_bump(
    previous: tuple[int, int, int], categories: set[str], breaking: bool
) -> str:
    if breaking or "Removed" in categories:
        return "major"
    if categories & {"Added", "Changed", "Deprecated"}:
        return "minor"
    return "patch"
