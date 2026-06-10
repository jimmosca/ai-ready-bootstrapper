"""Unit tests for the read-only sensor (`scripts/scan.py`), via fixture repos.

The sensor returns the `scan.json` payload as a plain dict; these tests assert
against that dict (the versioned interface the skill consumes).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scan import MAX_READ_BYTES, _command, _read_text, scan_repo


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "pyproject.toml",
        "[project]\nname='demo'\n[dependency-groups]\ndev=['pytest','ruff']\n",
    )
    _write(tmp_path / "README.md", "# demo\n")
    _write(tmp_path / "src" / "demo" / "__init__.py")
    _write(tmp_path / "src" / "demo" / "app.py", "print('hi')\n")
    _write(tmp_path / "tests" / "test_app.py", "def test_x():\n    assert True\n")
    return tmp_path


def test_refuses_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan_repo(tmp_path / "nope")


def test_inferred_command_must_carry_confidence():
    # The discipline of the retired CommandInfo invariant, kept on plain dicts.
    with pytest.raises(ValueError):
        _command("test", "pytest", "pyproject.toml", "inference", confidence=None)
    assert _command("test", "pytest", "pyproject.toml", "inference", "medium")["confidence"]


def test_inventory_basics(python_repo):
    result = scan_repo(python_repo)
    inv = result["repo"]
    assert result["schema_version"] == "0.1"
    assert inv["name"] == python_repo.name
    assert inv["root"] == str(python_repo.resolve())
    assert inv["vcs"] == "none"  # no .git in fixture
    assert inv["file_count"] == 5
    assert inv["languages"][0] == "Python"


def test_ignored_directories_are_pruned(python_repo):
    # Heavy/noisy dirs must not be walked or counted.
    _write(python_repo / "node_modules" / "left-pad" / "index.js", "module.exports=1\n")
    _write(python_repo / ".venv" / "pyvenv.cfg", "home = /usr\n")
    _write(python_repo / "__pycache__" / "app.cpython-312.pyc", "x")
    _write(python_repo / "dist" / "demo-0.1.whl", "x")

    result = scan_repo(python_repo)
    rels = {rel for paths in result["important_files"].values() for rel in paths}
    # File count is unchanged from the clean fixture: ignored dirs are skipped.
    assert result["repo"]["file_count"] == 5
    assert not any("node_modules" in r for r in rels)


def test_ai_dir_is_ignored_for_idempotency(python_repo):
    # A prior run's .ai/phase0/scan.json must not be counted or reported, so a
    # second scan yields identical output (the sensor reports the repo, not itself).
    _write(python_repo / ".ai" / "phase0" / "scan.json", "{}")
    result = scan_repo(python_repo)
    assert ".ai" not in result["excluded_dirs"]
    assert ".ai" not in result["top_level"]
    assert result["repo"]["file_count"] == 5


def test_detects_python_project_and_files(python_repo):
    result = scan_repo(python_repo)
    assert result["project_types"] == ["Python"]
    assert "README.md" in result["important_files"]["readme"]
    assert "pyproject.toml" in result["important_files"]["python_manifest"]
    assert "tests/test_app.py" in result["important_files"]["tests"]


def test_pyproject_commands_are_inferred(python_repo):
    result = scan_repo(python_repo)
    by_cmd = {c["command"]: c for c in result["commands"]}
    assert "pytest" in by_cmd
    assert by_cmd["pytest"]["finding_type"] == "inference"
    assert by_cmd["pytest"]["confidence"] is not None
    assert "ruff check" in by_cmd


def test_node_repo_scripts_are_facts(tmp_path):
    pkg = {"name": "web", "scripts": {"test": "vitest", "build": "tsc", "dev": "vite"}}
    _write(tmp_path / "package.json", json.dumps(pkg))
    _write(tmp_path / "src" / "index.ts", "export const x = 1\n")

    result = scan_repo(tmp_path)
    assert "Node/TypeScript" in result["project_types"]
    cmds = {c["command"]: c for c in result["commands"]}
    assert cmds["npm run test"]["finding_type"] == "fact"
    assert cmds["npm run test"]["category"] == "test"
    assert cmds["npm run build"]["category"] == "build"


def test_makefile_targets_are_facts(tmp_path):
    _write(tmp_path / "Makefile", ".PHONY: test\ntest:\n\tpytest\nlint:\n\truff check\n")
    result = scan_repo(tmp_path)
    cmds = {c["command"] for c in result["commands"]}
    assert "make test" in cmds
    assert "make lint" in cmds
    assert all(c["finding_type"] == "fact" for c in result["commands"])


def test_mixed_and_iac_and_dbt_detection(tmp_path):
    _write(tmp_path / "main.tf", 'resource "null_resource" "x" {}\n')
    _write(tmp_path / "app.py", "x = 1\n")
    _write(tmp_path / "package.json", json.dumps({"name": "w"}))
    _write(tmp_path / "dbt_project.yml", "name: analytics\n")
    _write(tmp_path / "notebooks" / "explore.ipynb", "{}")

    result = scan_repo(tmp_path)
    assert "Terraform/IaC" in result["project_types"]
    assert "dbt" in result["project_types"]
    assert "data pipeline" in result["project_types"]
    assert "mixed repo" in result["project_types"]
    assert "main.tf" in result["important_files"]["terraform"]
    assert "notebooks/explore.ipynb" in result["important_files"]["notebook"]


def test_head_commit_read_only_from_loose_ref(tmp_path):
    sha = "a" * 40
    _write(tmp_path / ".git" / "HEAD", "ref: refs/heads/main\n")
    _write(tmp_path / ".git" / "refs" / "heads" / "main", sha + "\n")
    _write(tmp_path / "README.md", "# x\n")

    result = scan_repo(tmp_path)
    assert result["repo"]["vcs"] == "git"
    assert result["repo"]["head_commit"] == sha
    # .git itself is ignored, so it contributes nothing to file_count.
    assert result["repo"]["file_count"] == 1


# --- glossary candidates (names, not meanings) -------------------------------


def test_glossary_candidates_propose_names_with_sources(python_repo):
    _write(python_repo / "src" / "demo" / "service.py", "class OrderService:\n    pass\n")
    cands = scan_repo(python_repo)["glossary_candidates"]
    by_term = {(c["term"], c["kind"]): c for c in cands}

    # A declaration becomes an identifier candidate, cited path:line.
    ident = by_term[("OrderService", "identifier")]
    assert ident["sources"] == ["src/demo/service.py:1"]
    # A non-generic directory ("demo") is a directory candidate; "src" is generic.
    assert ("demo", "directory") in by_term
    assert ("src", "directory") not in by_term
    # Candidates are ranked and capped.
    assert len(cands) <= 40


def test_glossary_skips_dotdirs_and_generic_dirs(python_repo):
    _write(python_repo / ".github" / "workflows" / "ci.yml", "on: push\n")
    terms = {c["term"] for c in scan_repo(python_repo)["glossary_candidates"]}
    assert ".github" not in terms
    assert "workflows" in terms  # a real dir name still surfaces


# --- state detection ---------------------------------------------------------


def test_state_virgin_repo(python_repo):
    state = scan_repo(python_repo)["state"]
    assert state["status"] == "virgin"
    assert state["signals"]["agents_md"] is False
    assert state["signals"]["upkeep_contract"] is False


def test_state_partial_when_some_surface_present(python_repo):
    _write(python_repo / "AGENTS.md", "# AGENTS\nno managed block here\n")
    state = scan_repo(python_repo)["state"]
    assert state["status"] == "partial"
    assert state["signals"]["agents_md"] is True


def test_state_already_bootstrapped(python_repo):
    _write(python_repo / "AGENTS.md", "# AGENTS\n## Upkeep Contract\nkeep it current\n")
    _write(python_repo / "CONTEXT.md", "# CONTEXT\n")
    _write(python_repo / "docs" / "adr" / "0001-foo.md", "# 0001\n")
    state = scan_repo(python_repo)["state"]
    assert state["status"] == "already-bootstrapped"
    assert state["signals"]["upkeep_contract"] is True
    assert state["signals"]["adr_dir"] is True


# --- safety: secret files, symlinks, binary, oversize ------------------------


def test_secret_files_are_flagged_not_read(python_repo):
    """Secret-bearing files are recorded by location but never read."""
    secret = python_repo / ".env"
    secret.write_text("API_TOKEN=super-secret-value\n")

    result = scan_repo(python_repo)
    assert ".env" in result["secret_files"]
    assert "super-secret-value" not in json.dumps(result)


def test_read_text_skips_secret_files(python_repo):
    secret = python_repo / "id_rsa"
    secret.write_text("-----BEGIN PRIVATE KEY-----\nMIIEv...\n")
    assert _read_text(secret) == ""


def test_read_text_skips_binary(tmp_path):
    blob = tmp_path / "image.bin"
    blob.write_bytes(b"\x89PNG\x00\x00\x00binary\x00data")
    assert _read_text(blob) == ""


def test_read_text_skips_oversize(tmp_path):
    big = tmp_path / "huge.txt"
    big.write_bytes(b"a" * (MAX_READ_BYTES + 10))
    assert _read_text(big) == ""


def test_walk_does_not_follow_symlinked_files(python_repo, tmp_path):
    """A symlinked file must not be read or counted (no escaping the repo)."""
    outside = tmp_path.parent / "outside_secret.txt"
    outside.write_text("OUTSIDE_SECRET\n")
    link = python_repo / "linked.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):  # pragma: no cover - no symlink support
        pytest.skip("symlinks unavailable on this platform")

    result = scan_repo(python_repo)
    rels = {p for paths in result["important_files"].values() for p in paths}
    assert "linked.txt" not in rels
    assert "OUTSIDE_SECRET" not in json.dumps(result)


def test_walk_does_not_follow_symlinked_dirs(python_repo, tmp_path):
    """A symlinked directory must not be descended into."""
    external = tmp_path.parent / "external_tree"
    (external / "deep").mkdir(parents=True, exist_ok=True)
    (external / "deep" / "leaked.py").write_text("print('leaked')\n")
    link = python_repo / "linkdir"
    try:
        link.symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):  # pragma: no cover - no symlink support
        pytest.skip("symlinks unavailable on this platform")

    result = scan_repo(python_repo)
    rels = {p for paths in result["important_files"].values() for p in paths}
    assert not any("linkdir" in r for r in rels)
