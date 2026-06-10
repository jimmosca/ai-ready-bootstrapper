"""End-to-end sensor tests over realistic, on-disk fixture repos.

Each directory under ``tests/fixtures/`` is a small but realistic repo of a given
ecosystem. These tests assert the sensor detects the right project type(s),
important files, and commands — all read-only. The fixtures are static inputs:
``scan_repo`` never writes, so running these tests does not touch them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from scan import scan_repo

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class Expectation:
    """What a fixture should produce, for parametrized assertions."""

    name: str
    project_types: list[str]  # exact set the sensor should report
    important: list[str]  # important-file categories that must be present
    state_status: str  # presence-based state hint
    absent_important: list[str] = field(default_factory=list)


EXPECTATIONS = [
    Expectation(
        name="python_fastapi_repo",
        project_types=["Python"],
        important=["readme", "python_manifest", "tests", "dockerfile", "github_actions"],
        state_status="virgin",
    ),
    Expectation(
        name="node_typescript_repo",
        project_types=["Node/TypeScript"],
        important=["readme", "node_manifest", "tests"],
        state_status="virgin",
    ),
    Expectation(
        name="terraform_repo",
        project_types=["Terraform/IaC"],
        important=["readme", "terraform"],
        state_status="virgin",
    ),
    Expectation(
        name="dbt_repo",
        project_types=["dbt"],
        important=["readme", "dbt"],
        state_status="virgin",
    ),
    Expectation(
        name="mixed_data_ai_repo",
        project_types=["Python", "Terraform/IaC", "mixed repo"],
        important=["readme", "agents", "docker_compose", "terraform", "tests", "python_manifest"],
        # AGENTS.md fixture is present but has no Upkeep Contract → partial.
        state_status="partial",
    ),
]

IDS = [e.name for e in EXPECTATIONS]


def test_all_fixtures_exist():
    for exp in EXPECTATIONS:
        assert (FIXTURES / exp.name).is_dir(), f"missing fixture: {exp.name}"


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_project_type_detection(exp: Expectation):
    result = scan_repo(FIXTURES / exp.name)
    assert result["project_types"] == exp.project_types


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_important_files_detected(exp: Expectation):
    result = scan_repo(FIXTURES / exp.name)
    found = set(result["important_files"])
    missing = set(exp.important) - found
    assert not missing, f"{exp.name}: missing important categories {sorted(missing)}"
    # Every detected path is real and relative to the repo.
    for paths in result["important_files"].values():
        for rel in paths:
            assert (FIXTURES / exp.name / rel).exists()


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_state_status(exp: Expectation):
    result = scan_repo(FIXTURES / exp.name)
    assert result["state"]["status"] == exp.state_status


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=IDS)
def test_glossary_candidates_are_named_with_sources(exp: Expectation):
    cands = scan_repo(FIXTURES / exp.name)["glossary_candidates"]
    assert cands, f"{exp.name}: expected at least one glossary candidate"
    for c in cands:
        assert c["term"] and c["kind"] in {"directory", "identifier", "readme"}
        assert c["sources"], f"{c['term']} has no source"


def test_node_scripts_are_facts():
    result = scan_repo(FIXTURES / "node_typescript_repo")
    cmds = {c["command"]: c for c in result["commands"]}
    assert cmds["npm run test"]["finding_type"] == "fact"
    assert cmds["npm run build"]["category"] == "build"


def test_python_commands_are_inferred_with_confidence():
    result = scan_repo(FIXTURES / "python_fastapi_repo")
    cmds = {c["command"]: c for c in result["commands"]}
    assert "pytest" in cmds
    assert cmds["pytest"]["finding_type"] == "inference"
    assert cmds["pytest"]["confidence"] is not None


def test_scan_repo_is_read_only(tmp_path):
    """scan_repo must not create anything inside the target tree (it is pure)."""
    repo = FIXTURES / "python_fastapi_repo"
    before = {p.relative_to(repo) for p in repo.rglob("*")}
    scan_repo(repo)
    after = {p.relative_to(repo) for p in repo.rglob("*")}
    assert before == after
    assert not (repo / ".ai").exists()  # no write into the target repo


def test_scan_is_deterministic():
    """Same input → same output (the sensor's core guarantee)."""
    repo = FIXTURES / "mixed_data_ai_repo"
    assert scan_repo(repo) == scan_repo(repo)
