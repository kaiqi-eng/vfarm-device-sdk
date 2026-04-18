from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT / "pyproject.toml"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
MATRIX_PATH = ROOT / "contracts" / "sdk_compatibility_matrix.json"


def _load_project_metadata() -> tuple[str, str]:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project = data.get("project", {})
    name = project.get("name")
    version = project.get("version")
    if not isinstance(name, str) or not isinstance(version, str):
        raise RuntimeError("Could not read project.name/project.version from pyproject.toml")
    return name, version


def _git_tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list", "v*", "--sort=v:refname"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tags = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return tags


def _extract_version_from_tag(tag: str) -> str | None:
    match = re.fullmatch(r"v(?P<version>\d+\.\d+\.\d+(?:[a-zA-Z0-9.\-+]*)?)", tag)
    if not match:
        return None
    return match.group("version")


def _latest_release_tag(tags: list[str]) -> str | None:
    semantic = [tag for tag in tags if _extract_version_from_tag(tag)]
    if not semantic:
        return None
    return semantic[-1]


def _check_version_changed(current_version: str, tags: list[str]) -> None:
    latest = _latest_release_tag(tags)
    if not latest:
        return
    latest_version = _extract_version_from_tag(latest)
    if latest_version == current_version:
        raise RuntimeError(
            f"Version has not changed since latest release tag {latest}. "
            f"Bump project.version before publishing."
        )


def _check_tag_matches_version(current_version: str, tag: str | None, require_tag: bool) -> None:
    if require_tag and not tag:
        raise RuntimeError("Release tag is required but was not provided.")
    if not tag:
        return
    expected = f"v{current_version}"
    if tag != expected:
        raise RuntimeError(f"Release tag mismatch: expected {expected}, got {tag}")


def _check_changelog_has_version(current_version: str) -> None:
    if not CHANGELOG_PATH.exists():
        raise RuntimeError("CHANGELOG.md is missing.")
    content = CHANGELOG_PATH.read_text(encoding="utf-8")
    patterns = [
        rf"^##\s+\[{re.escape(current_version)}\]",
        rf"^##\s+{re.escape(current_version)}\b",
    ]
    if not any(re.search(pattern, content, flags=re.MULTILINE) for pattern in patterns):
        raise RuntimeError(f"CHANGELOG.md does not contain an entry for version {current_version}.")


def _package_version_exists(package_name: str, version: str, target: str) -> bool:
    base = "https://test.pypi.org" if target == "testpypi" else "https://pypi.org"
    url = f"{base}/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise RuntimeError(f"Failed to query {target} package index: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to query {target} package index: {exc.reason}") from exc

    releases = payload.get("releases", {})
    return version in releases and bool(releases[version])


def _check_matrix_entry(current_version: str) -> None:
    if not MATRIX_PATH.exists():
        raise RuntimeError(f"Compatibility matrix missing: {MATRIX_PATH}")
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8-sig"))
    entries = payload.get("entries", [])
    for entry in entries:
        if entry.get("sdk_version") == current_version:
            return
    raise RuntimeError(
        f"contracts/sdk_compatibility_matrix.json is missing sdk_version={current_version} entry."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release discipline checks before publish.")
    parser.add_argument("--target", choices=["testpypi", "pypi"], required=True)
    parser.add_argument("--tag", default=None, help="Release tag (for example v0.1.2).")
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--skip-index-check", action="store_true")
    args = parser.parse_args()

    package_name, current_version = _load_project_metadata()
    tags = _git_tags()

    _check_version_changed(current_version, tags)
    _check_tag_matches_version(current_version, args.tag, args.require_tag)
    _check_changelog_has_version(current_version)
    _check_matrix_entry(current_version)

    if not args.skip_index_check and _package_version_exists(package_name, current_version, args.target):
        raise RuntimeError(
            f"{package_name}=={current_version} already exists on {args.target}; "
            "bump version before publish."
        )

    print("release_guard: all checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"release_guard: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
