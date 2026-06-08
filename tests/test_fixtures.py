"""End-to-end tests over realistic, on-disk fixture repos.

Each directory under ``tests/fixtures/`` is a small but realistic repo of a
given ecosystem. These tests assert the scanner detects the right project
type(s) and important files, and that the renderer produces a complete,
evidence-backed pack with *sensible* risks and open questions — all read-only.

The fixtures are static inputs only: they are never installed or executed, and
``build_pack`` never writes, so running these tests does not touch the fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from phase0_bootstrapper.models import FindingType, ScanTarget
from phase0_bootstrapper.renderer import ALL_FILES, build_pack, generate
from phase0_bootstrapper.scanner import scan_repo

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class Expectation:
    """What a fixture should produce, for parametrized assertions."""

    name: str
    project_types: list[str]  # exact set the scanner should report
    important: list[str]  # important-file categories that must be present
    risk_categories: list[str]  # risk categories that must appear
    absent_risk_categories: list[str] = ()  # categories that must NOT appear


EXPECTATIONS = [
    Expectation(
        name="python_fastapi_repo",
        project_types=["Python"],
        important=["readme", "python_manifest", "tests", "dockerfile", "github_actions"],
        risk_categories=[],
        # Has tests and CI, so these are correctly NOT flagged.
        absent_risk_categories=["testing-gap", "build-ci"],
    ),
    Expectation(
        name="node_typescript_repo",
        project_types=["Node/TypeScript"],
        important=["readme", "node_manifest", "tests"],
        risk_categories=["build-ci"],  # no CI workflow present
    ),
    Expectation(
        name="terraform_repo",
        project_types=["Terraform/IaC"],
        important=["readme", "terraform"],
        risk_categories=["testing-gap", "verification", "build-ci"],
    ),
    Expectation(
        name="dbt_repo",
        project_types=["dbt"],
        important=["readme", "dbt"],
        risk_categories=["testing-gap", "build-ci"],
    ),
    Expectation(
        name="mixed_data_ai_repo",
        project_types=["Python", "Terraform/IaC", "mixed repo"],
        important=["readme", "agents", "docker_compose", "terraform", "tests", "python_manifest"],
        risk_categories=["build-ci"],  # python tests exist, but no CI
        absent_risk_categories=["testing-gap"],
    ),
]

IDS = [e.name for e in EXPECTATIONS]


def _pack(name: str, output_dir: Path):
    repo = FIXTURES / name
    return build_pack(ScanTarget(repo_path=repo, output_dir=output_dir))


def test_all_fixtures_exist():
    for exp in EXPECTATIONS:
        assert (FIXTURES / exp.name).is_dir(), f"missing fixture: {exp.name}"


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_project_type_detection(exp: Expectation):
    scan = scan_repo(FIXTURES / exp.name)
    assert scan.project_types == exp.project_types


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_important_files_detected(exp: Expectation):
    scan = scan_repo(FIXTURES / exp.name)
    found = set(scan.important_files)
    missing = set(exp.important) - found
    assert not missing, f"{exp.name}: missing important categories {sorted(missing)}"
    # Every detected path is real and relative to the repo.
    for paths in scan.important_files.values():
        for rel in paths:
            assert (FIXTURES / exp.name / rel).exists()


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_renderer_produces_complete_pack(exp: Expectation, tmp_path):
    pack = _pack(exp.name, tmp_path / "out")
    # All 11 files render and are non-empty.
    assert set(pack.files) == set(ALL_FILES)
    assert all(content.strip() for content in pack.files.values())
    # Evidence references all resolve (the traceability guarantee).
    pack.report.validate()
    # Read-only invariant: a report is meaningful — at least one finding.
    assert pack.report.findings
    assert pack.report.findings_by_type(FindingType.FACT)
    # Manifest records read-only mode.
    assert "mode: read-only" in pack.files["manifest.yaml"]


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_sensible_risks(exp: Expectation, tmp_path):
    pack = _pack(exp.name, tmp_path / "out")
    categories = {r.category for r in pack.report.risks}
    for expected in exp.risk_categories:
        assert expected in categories, f"{exp.name}: expected risk '{expected}'"
    for absent in exp.absent_risk_categories:
        assert absent not in categories, f"{exp.name}: unexpected risk '{absent}'"
    # Any risk that exists must be backed by evidence and rendered.
    register = pack.files["risk-register.md"]
    for risk in pack.report.risks:
        assert risk.evidence, f"{risk.id} has no evidence"
        assert risk.id in register


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_open_questions_present_and_rendered(exp: Expectation, tmp_path):
    pack = _pack(exp.name, tmp_path / "out")
    assert pack.report.open_questions  # every fixture yields unknowns to resolve
    doc = pack.files["assumptions-and-open-questions.md"]
    for q in pack.report.open_questions:
        assert q.id in doc


def test_node_scripts_are_facts():
    scan = scan_repo(FIXTURES / "node_typescript_repo")
    cmds = {c.command: c for c in scan.commands}
    assert cmds["npm run test"].finding_type is FindingType.FACT
    assert cmds["npm run build"].category == "build"


def test_python_commands_are_inferred_with_confidence():
    scan = scan_repo(FIXTURES / "python_fastapi_repo")
    cmds = {c.command: c for c in scan.commands}
    assert "pytest" in cmds
    assert cmds["pytest"].finding_type is FindingType.INFERENCE
    assert cmds["pytest"].confidence is not None


def test_generate_is_read_only_writing_only_the_output_dir(tmp_path):
    """Rendering to disk must not create anything inside the fixture tree."""
    repo = FIXTURES / "python_fastapi_repo"
    before = {p.relative_to(repo) for p in repo.rglob("*")}

    out = tmp_path / "pack"
    written = generate(
        ScanTarget(repo_path=repo, output_dir=out),
        generated_at="2026-06-08T00:00:00Z",
    )

    assert {p.name for p in written} == set(ALL_FILES)
    assert not (repo / ".ai").exists()  # no write into the target repo
    after = {p.relative_to(repo) for p in repo.rglob("*")}
    assert before == after  # fixture tree is byte-for-byte unchanged in shape
