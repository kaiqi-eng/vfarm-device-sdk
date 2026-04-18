from __future__ import annotations

import importlib.util
import json
import urllib.error
from io import BytesIO
from pathlib import Path

import pytest


def _load_release_guard_module():
    root = Path(__file__).resolve().parents[2]
    script_path = root / "scripts" / "release_guard.py"
    spec = importlib.util.spec_from_file_location("release_guard", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load release_guard module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_guard_detects_unchanged_version() -> None:
    guard = _load_release_guard_module()
    with pytest.raises(RuntimeError, match="Version has not changed"):
        guard._check_version_changed("0.1.1", ["v0.1.0", "v0.1.1"])


def test_release_guard_tag_must_match_version() -> None:
    guard = _load_release_guard_module()
    with pytest.raises(RuntimeError, match="Release tag mismatch"):
        guard._check_tag_matches_version("0.1.2", "v0.1.3", require_tag=True)


def test_release_guard_accepts_matching_changelog_and_matrix(tmp_path: Path) -> None:
    guard = _load_release_guard_module()

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [0.2.0] - 2026-04-18\n", encoding="utf-8")
    guard.CHANGELOG_PATH = changelog
    guard._check_changelog_has_version("0.2.0")

    matrix = tmp_path / "sdk_compatibility_matrix.json"
    matrix.write_text(
        json.dumps({"entries": [{"sdk_version": "0.2.0"}]}),
        encoding="utf-8",
    )
    guard.MATRIX_PATH = matrix
    guard._check_matrix_entry("0.2.0")


def test_release_guard_index_check_404_is_not_published(monkeypatch: pytest.MonkeyPatch) -> None:
    guard = _load_release_guard_module()

    def _fake_urlopen(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise urllib.error.HTTPError(args[0], 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr(guard.urllib.request, "urlopen", _fake_urlopen)
    assert guard._package_version_exists("vfarm-device-sdk", "99.9.9", "testpypi") is False


def test_release_guard_index_check_detects_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    guard = _load_release_guard_module()
    payload = {"releases": {"0.1.1": [{"filename": "vfarm_device_sdk-0.1.1.tar.gz"}]}}

    class _Response:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return False

        def read(self) -> bytes:
            return BytesIO(json.dumps(payload).encode("utf-8")).read()

    def _fake_urlopen(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _Response()

    monkeypatch.setattr(guard.urllib.request, "urlopen", _fake_urlopen)
    assert guard._package_version_exists("vfarm-device-sdk", "0.1.1", "pypi") is True
