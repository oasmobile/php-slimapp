import re
from pathlib import Path
from typing import Any

from mdf_core.foundation.constants import (
    CHANGELOG_UNRELEASED_ENTRY_RE,
    CHANGELOG_UNRELEASED_HEADING_RE,
    is_unreleased_heading,
)
from mdf_core.foundation.errors import Finding, MDFError, add_finding
from mdf_core.foundation.paths import path_stays_in_repo, relative
from mdf_core.foundation.semver import bump_kind, required_bump
from mdf_core.foundation.textutil import stable_semver
from mdf_core.foundation.yamlutil import read_frontmatter


def validate_changelog(repo: Path, findings: list[Finding]) -> None:
    path = repo / "CHANGELOG.md"
    if not path.is_file():
        add_finding(
            findings,
            "changelog.missing",
            "Missing release-only CHANGELOG.md",
            "CHANGELOG.md",
        )
        return
    if path.is_symlink() or not path_stays_in_repo(repo, path):
        add_finding(
            findings,
            "path.symlink",
            "CHANGELOG.md must be a regular repository file",
            "CHANGELOG.md",
        )
        return
    text = path.read_text(encoding="utf-8")
    if CHANGELOG_UNRELEASED_HEADING_RE.search(text):
        add_finding(
            findings,
            "changelog.unreleased",
            "Root CHANGELOG must not contain an Unreleased section",
            "CHANGELOG.md",
        )
    if CHANGELOG_UNRELEASED_ENTRY_RE.search(text):
        add_finding(
            findings,
            "version.sentinel_scope",
            "unreleased is forbidden in CHANGELOG",
            "CHANGELOG.md",
        )


def changelog_versions(repo: Path, findings: list[Finding]) -> list[str]:
    path = repo / "CHANGELOG.md"
    if not path.is_file() or path.is_symlink():
        return []
    versions: list[str] = []
    for match in re.finditer(
        r"^##\s+(?:\[([^\]]+)\]|(\S+))(?:\s+-\s+.*)?$",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        value = match.group(1) or match.group(2)
        if is_unreleased_heading(value):
            continue
        if stable_semver(value) is None:
            add_finding(
                findings,
                "changelog.version",
                f"CHANGELOG release heading must use stable SemVer: {value}",
                "CHANGELOG.md",
            )
            continue
        if value in versions:
            add_finding(
                findings,
                "changelog.version_duplicate",
                f"Duplicate CHANGELOG release: {value}",
                "CHANGELOG.md",
            )
            continue
        versions.append(value)
    parsed = [stable_semver(version) for version in versions]
    if parsed != sorted(parsed, reverse=True):
        add_finding(
            findings,
            "changelog.order",
            "CHANGELOG releases must be ordered newest first",
            "CHANGELOG.md",
        )
    return versions


def change_release_profile(path: Path) -> tuple[set[str], bool]:
    metadata, _ = read_frontmatter(path)
    release_notes = metadata.get("release_notes")
    categories = (
        {
            key
            for key, value in release_notes.items()
            if isinstance(value, list) and value
        }
        if isinstance(release_notes, dict)
        else set()
    )
    return categories, metadata.get("breaking") is True


def validate_release_history(
    repo: Path,
    manifest: dict[str, Any] | None,
    findings: list[Finding],
) -> None:
    changelog = changelog_versions(repo, findings)
    changelog_set = set(changelog)
    release_root = repo / "changes"
    release_dirs = (
        sorted(
            (
                path
                for path in release_root.iterdir()
                if path.is_dir()
                and not path.is_symlink()
                and stable_semver(path.name) is not None
            ),
            key=lambda path: stable_semver(path.name),
        )
        if release_root.is_dir()
        else []
    )
    release_versions = [path.name for path in release_dirs]
    for version in release_versions:
        if version not in changelog_set:
            add_finding(
                findings,
                "release.changelog_missing",
                f"Released version is missing from CHANGELOG: {version}",
                f"changes/{version}",
            )

    latest_release: Any = None
    if manifest is not None:
        versioning = manifest.get("versioning")
        if isinstance(versioning, dict):
            latest_release = versioning.get("latest_release")
    known_versions = {
        version
        for version in (*changelog, *release_versions)
        if stable_semver(version) is not None
    }
    if latest_release is None and known_versions:
        add_finding(
            findings,
            "manifest.latest_release_history",
            "versioning.latest_release is null but stable release records "
            "exist",
            ".mdf/manifest.yaml",
        )
    elif stable_semver(latest_release) is not None:
        if not known_versions:
            add_finding(
                findings,
                "manifest.latest_release_history",
                f"latest_release {latest_release} has no CHANGELOG or "
                "version CHANGE record",
                ".mdf/manifest.yaml",
            )
        else:
            expected_latest = max(
                known_versions,
                key=lambda version: stable_semver(version),
            )
            if latest_release != expected_latest:
                add_finding(
                    findings,
                    "manifest.latest_release_history",
                    (
                        f"latest_release {latest_release} disagrees with "
                        f"release history; expected {expected_latest}"
                    ),
                    ".mdf/manifest.yaml",
                )

    ordered_changelog = sorted(
        changelog_set, key=lambda version: stable_semver(version)
    )
    for release_dir in release_dirs:
        version = release_dir.name
        release_file = release_dir / "CHANGE.md"
        if not release_file.is_file():
            continue
        try:
            release_metadata, _ = read_frontmatter(release_file)
        except MDFError:
            continue
        prior_changelog = [
            item
            for item in ordered_changelog
            if stable_semver(item) < stable_semver(version)
        ]
        expected_previous = prior_changelog[-1] if prior_changelog else "none"
        actual_previous = release_metadata.get("previous_version")
        if actual_previous != expected_previous:
            add_finding(
                findings,
                "release.previous_chain",
                (
                    f"Version CHANGE previous_version is {actual_previous!r}; "
                    f"expected {expected_previous!r}"
                ),
                relative(repo, release_file),
            )

        change_files = sorted(
            path / "CHANGE.md"
            for path in release_dir.iterdir()
            if path.is_dir() and not path.is_symlink()
        )
        existing_changes = [path for path in change_files if path.is_file()]
        categories: set[str] = set()
        breaking = False
        profile_valid = True
        for change in [release_file, *existing_changes]:
            try:
                change_categories, change_breaking = change_release_profile(
                    change
                )
            except MDFError:
                profile_valid = False
                continue
            categories.update(change_categories)
            breaking = breaking or change_breaking
        if not profile_valid:
            continue
        previous_tuple = (
            (0, 0, 0)
            if actual_previous == "none"
            else stable_semver(actual_previous)
        )
        candidate_tuple = stable_semver(version)
        if previous_tuple is None or candidate_tuple is None:
            continue
        try:
            actual_bump = bump_kind(previous_tuple, candidate_tuple)
        except MDFError as exc:
            add_finding(
                findings,
                "release.version_order",
                str(exc),
                relative(repo, release_file),
            )
            continue
        required = required_bump(
            previous_tuple, categories or {"none"}, breaking
        )
        rank = {"patch": 1, "minor": 2, "major": 3}
        if rank[actual_bump] < rank[required]:
            add_finding(
                findings,
                "release.semver",
                (
                    f"Release {version} uses a {actual_bump} bump but its "
                    f"Change set requires at least {required}"
                ),
                relative(repo, release_file),
            )
