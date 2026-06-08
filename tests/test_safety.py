"""Unit tests for the read-only safety guardrails."""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0_bootstrapper.safety import (
    DEFAULT_OUTPUT_SUBDIR,
    IGNORED_DIRS,
    ensure_safe_output_dir,
    ensure_safe_repo_path,
    is_dangerous_root,
    is_ignored_dir,
    is_secret_file,
    looks_binary,
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


# --- symlink handling --------------------------------------------------------


def test_symlink_to_system_root_is_refused(tmp_path):
    """A symlink pointing at a forbidden root must be caught after resolution."""
    link = tmp_path / "sneaky"
    try:
        link.symlink_to("/etc")
    except (OSError, NotImplementedError):  # pragma: no cover - platform without symlinks
        pytest.skip("symlinks unavailable on this platform")
    with pytest.raises(ValueError):
        ensure_safe_repo_path(link)


def test_dangerous_root_predicate(tmp_path):
    assert is_dangerous_root("/")
    assert is_dangerous_root("/etc")
    assert is_dangerous_root(Path.home())
    assert not is_dangerous_root(tmp_path)


# --- secret-file detection ---------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.production",
        ".env.local",
        "id_rsa",
        "id_ed25519",
        "server.pem",
        "private.key",
        "store.p12",
        "app.keystore",
        ".npmrc",
        ".netrc",
        ".pgpass",
        "credentials.json",
        "secrets.yaml",
        "token.secret",
    ],
)
def test_secret_files_are_flagged(name):
    assert is_secret_file(name)


@pytest.mark.parametrize(
    "name",
    [
        ".env.example",
        ".env.sample",
        ".env.template",
        "id_rsa.pub",
        "config.yaml",
        "main.py",
        "README.md",
        "package.json",
    ],
)
def test_non_secret_files_are_not_flagged(name):
    assert not is_secret_file(name)


# --- binary detection --------------------------------------------------------


def test_looks_binary_detects_nul_byte():
    assert looks_binary(b"\x89PNG\x00\x00data")
    assert not looks_binary(b"plain text, no nul")
    assert not looks_binary(b"")


# --- output-dir validation ---------------------------------------------------


def test_output_dir_inside_ai_tree_is_allowed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    out = repo / ".ai" / "phase0"
    assert ensure_safe_output_dir(out, repo) == out.resolve()


def test_output_dir_outside_repo_is_allowed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    out = tmp_path / "elsewhere" / "pack"
    assert ensure_safe_output_dir(out, repo) == out.resolve()


def test_output_dir_equal_to_repo_root_is_refused(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError):
        ensure_safe_output_dir(repo, repo)


def test_output_dir_inside_repo_outside_ai_is_refused(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    with pytest.raises(ValueError):
        ensure_safe_output_dir(repo / "src" / "pack", repo)


def test_output_dir_system_root_is_refused(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError):
        ensure_safe_output_dir("/etc", repo)
