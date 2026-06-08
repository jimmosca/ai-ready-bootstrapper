"""Tests for the Phase 0 renderer: file creation + evidence/confidence content."""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0_bootstrapper.models import ScanTarget
from phase0_bootstrapper.renderer import ALL_FILES, generate, render
from phase0_bootstrapper.scanner import scan_repo


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "pyproject.toml",
        "[project]\nname='demo'\n[tool.ruff]\n[tool.pytest.ini_options]\n",
    )
    _write(tmp_path / "README.md", "# demo\n")
    _write(tmp_path / "src" / "demo" / "app.py", "print('hi')\n")
    _write(tmp_path / "tests" / "test_app.py", "def test_x():\n    assert True\n")
    return tmp_path


def test_render_produces_all_files(python_repo):
    files = render(scan_repo(python_repo), generated_at="2026-06-08T00:00:00Z")
    assert set(files) == set(ALL_FILES)
    assert all(content.strip() for content in files.values())


def test_generate_writes_all_files_to_disk(python_repo, tmp_path):
    out = tmp_path / "pack"
    target = ScanTarget(repo_path=python_repo, output_dir=out)
    written = generate(target, generated_at="2026-06-08T00:00:00Z")

    assert {p.name for p in written} == set(ALL_FILES)
    for name in ALL_FILES:
        assert (out / name).is_file()


def test_manifest_is_read_only_and_versioned(python_repo):
    files = render(scan_repo(python_repo), generated_at="2026-06-08T00:00:00Z")
    manifest = files["manifest.yaml"]
    assert "mode: read-only" in manifest
    assert "generated_at: \"2026-06-08T00:00:00Z\"" in manifest
    assert "overall_confidence:" in manifest
    assert "analyzed_areas:" in manifest
    assert "excluded_areas:" in manifest


def test_evidence_map_resolves_referenced_ids(python_repo):
    files = render(scan_repo(python_repo), generated_at="2026-06-08T00:00:00Z")
    emap = files["evidence-map.md"]
    # Evidence ids cited in repo-map must appear as rows in evidence-map.
    assert "| E1 |" in emap
    # repo-map cites at least one E# that the evidence map defines.
    assert "Evidence" in files["repo-map.md"]


def test_inferred_commands_carry_confidence(python_repo):
    files = render(scan_repo(python_repo), generated_at="2026-06-08T00:00:00Z")
    tooling = files["commands-and-tooling.md"]
    assert "pytest" in tooling
    # the pyproject-inferred pytest command is tagged inference with a confidence
    assert "inference" in tooling
    assert "medium" in tooling or "low" in tooling


def test_risk_register_has_severity_confidence_and_evidence(tmp_path):
    # A bare repo: no tests, no commands, no CI -> concrete risks with backing.
    _write(tmp_path / "notes.txt", "hello")
    files = render(scan_repo(tmp_path), generated_at="2026-06-08T00:00:00Z")
    risks = files["risk-register.md"]
    assert "Severity" in risks and "Confidence" in risks and "Mitigation" in risks
    assert "No tests detected" in risks
    assert "E1" in risks  # evidence id cited


def test_entrypoints_marked_not_executed(tmp_path):
    _write(tmp_path / "package.json", '{"name":"w","scripts":{"dev":"vite","build":"tsc"}}')
    files = render(scan_repo(tmp_path), generated_at="2026-06-08T00:00:00Z")
    ep = files["entrypoints.md"]
    assert "detected, not executed" in ep.lower()


def test_decision_log_backed_by_evidence_no_inventions(python_repo):
    files = render(scan_repo(python_repo), generated_at="2026-06-08T00:00:00Z")
    log = files["decision-log.md"]
    assert "Evidence:" in log
    assert "Confidence:" in log


def test_bare_repo_still_renders_with_explicit_unknowns(tmp_path):
    _write(tmp_path / "data.csv", "a,b\n1,2\n")
    files = render(scan_repo(tmp_path), generated_at="2026-06-08T00:00:00Z")
    assert set(files) == set(ALL_FILES)
    # Uncertainty is explicit, not hidden.
    assert "[OPEN]" in files["repo-map.md"]
    assert "unknown" in files["agent-handoff.md"].lower()
