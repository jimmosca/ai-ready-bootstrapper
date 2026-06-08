"""Unit tests for the read-only safety guardrails."""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0_bootstrapper.safety import (
    DEFAULT_OUTPUT_SUBDIR,
    IGNORED_DIRS,
    ensure_safe_repo_path,
    is_ignored_dir,
)


def test_output_subdir_is_ai_phase0():
    assert DEFAULT_OUTPUT_SUBDIR == Path(".ai") / "phase0"


def test_ignored_dirs_cover_the_required_set():
    required = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "target",
        "__pycache__",
    }
    assert required <= IGNORED_DIRS
    assert is_ignored_dir("node_modules")
    assert not is_ignored_dir("src")


def test_empty_path_is_refused():
    with pytest.raises(ValueError):
        ensure_safe_repo_path("")
    with pytest.raises(ValueError):
        ensure_safe_repo_path("   ")


def test_missing_path_is_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        ensure_safe_repo_path(tmp_path / "does-not-exist")


def test_file_is_refused(tmp_path):
    f = tmp_path / "a-file.txt"
    f.write_text("hi")
    with pytest.raises(ValueError):
        ensure_safe_repo_path(f)


@pytest.mark.parametrize("dangerous", ["/", "/home", "/etc", "/usr"])
def test_system_roots_are_refused(dangerous):
    with pytest.raises(ValueError):
        ensure_safe_repo_path(dangerous)


def test_home_directory_is_refused():
    with pytest.raises(ValueError):
        ensure_safe_repo_path(Path.home())


def test_valid_directory_is_resolved(tmp_path):
    resolved = ensure_safe_repo_path(tmp_path)
    assert resolved == tmp_path.resolve()
    assert resolved.is_dir()
