import re
import secrets
import unicodedata
from typing import Any

from mdf_core.foundation.constants import OBJECT_ID_SLUG_RE, STABLE_SEMVER_RE
from mdf_core.foundation.errors import MDFError


def stable_semver(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = STABLE_SEMVER_RE.fullmatch(value)
    if not match:
        return None
    return tuple(  # type: ignore[return-value]
        int(part) for part in match.groups()
    )


def slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    normalized = normalized.replace("/", "-")
    normalized = normalized.replace("_", "-").replace(".", "-")
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise MDFError(
            "Slug becomes empty after normalization", code="empty_slug"
        )
    return normalized


def is_object_id_slug(value: str) -> bool:
    return OBJECT_ID_SLUG_RE.fullmatch(value) is not None


_ID_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_ID_DIGITS = "0123456789"
_ID_ALPHABET = _ID_LETTERS + _ID_DIGITS


def new_prp_id() -> str:
    """生成四位随机 PRP ID：前两位数字，后两位最多一个字母。"""
    while True:
        suffix = "".join(secrets.choice(_ID_ALPHABET) for _ in range(2))
        if not suffix.isalpha():
            prefix = "".join(secrets.choice(_ID_DIGITS) for _ in range(2))
            return f"prp-{prefix}{suffix}"


def new_short_id() -> str:
    """生成四位短 ID：字符集与校验相同，但至少含一个字母和一个数字。"""
    letters = set(_ID_LETTERS)
    digits = set(_ID_DIGITS)
    while True:
        value = "".join(secrets.choice(_ID_ALPHABET) for _ in range(4))
        chars = set(value)
        if chars & letters and chars & digits:
            return value
