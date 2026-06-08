"""Unit tests for the Phase 0 data model. Behavior only — no scanner logic."""

from __future__ import annotations

import pytest

from phase0_bootstrapper.models import (
    SCHEMA_VERSION,
    CommandInfo,
    ConfidenceLevel,
    Decision,
    Entrypoint,
    Evidence,
    EvidenceKind,
    Finding,
    FindingType,
    OpenQuestion,
    Phase0Report,
    RepoInventory,
    Risk,
)


def _ev(eid: str = "E1") -> Evidence:
    return Evidence(id=eid, claim="uses vitest", source="package.json:31")


def test_enums_are_string_valued():
    assert FindingType.FACT.value == "fact"
    assert ConfidenceLevel.HIGH.value == "high"
    assert EvidenceKind.COMMAND == "command"  # str-Enum compares to its value


def test_evidence_renders_map_row():
    ev = Evidence(id="E1", claim="test runner", source="package.json:31", kind=EvidenceKind.CONFIG)
    assert ev.as_row() == "| E1 | test runner | package.json:31 | config |"


def test_fact_requires_evidence():
    with pytest.raises(ValueError):
        Finding(type=FindingType.FACT, statement="has a Makefile")
    # ok with evidence
    f = Finding(type=FindingType.FACT, statement="has a Makefile", evidence=["E1"])
    assert f.evidence == ["E1"]


def test_inference_requires_confidence():
    with pytest.raises(ValueError):
        Finding(type=FindingType.INFERENCE, statement="HTTP layer is Express", evidence=["E1"])
    f = Finding(
        type=FindingType.INFERENCE,
        statement="HTTP layer is Express",
        evidence=["E1"],
        confidence=ConfidenceLevel.HIGH,
    )
    assert f.confidence is ConfidenceLevel.HIGH


def test_assumption_and_open_need_neither():
    a = Finding(
        type=FindingType.ASSUMPTION,
        statement="Postgres is prod DB",
        confirm_refute="check infra/",
        impact_if_wrong=ConfidenceLevel.HIGH,
    )
    q = Finding(type=FindingType.OPEN, statement="who owns auth rotation?")
    assert a.confidence is None and not q.evidence


def test_command_inference_requires_confidence():
    with pytest.raises(ValueError):
        CommandInfo(
            category="test",
            command="pytest",
            source="README.md:10",
            finding_type=FindingType.INFERENCE,
        )
    # FACT command (found in source) is fine without confidence
    c = CommandInfo(category="test", command="pytest", source="pyproject.toml:30")
    assert c.finding_type is FindingType.FACT


def test_entrypoint_location():
    assert Entrypoint(path="src/app.py", kind="server", line=12).location == "src/app.py:12"
    assert Entrypoint(path="src/app.py", kind="server").location == "src/app.py"


def test_decision_always_has_confidence():
    d = Decision(id="D1", decision="uses Postgres via Prisma", why="schema present")
    assert d.confidence is ConfidenceLevel.LOW


def test_report_defaults_and_filtering():
    report = Phase0Report(inventory=RepoInventory(name="demo", root="/r"))
    assert report.schema_version == SCHEMA_VERSION
    assert report.generator == "phase0-bootstrapper"

    fact = Finding(type=FindingType.FACT, statement="has CI", evidence=["E1"])
    assumption = Finding(type=FindingType.ASSUMPTION, statement="single deploy target")
    report.findings.extend([fact, assumption])
    assert report.findings_by_type(FindingType.FACT) == [fact]


def test_report_evidence_resolution():
    report = Phase0Report()
    report.evidence.append(_ev("E1"))
    report.findings.append(Finding(type=FindingType.FACT, statement="vitest", evidence=["E1"]))
    report.risks.append(
        Risk(
            id="R1",
            risk="no tests",
            category="testing-gap",
            likelihood=ConfidenceLevel.MEDIUM,
            impact=ConfidenceLevel.HIGH,
            evidence=["E9"],  # dangling
        )
    )
    assert report.unresolved_evidence_refs() == {"E9"}
    with pytest.raises(ValueError):
        report.validate()

    report.evidence.append(Evidence(id="E9", claim="no tests dir", source="git ls-files"))
    report.validate()  # now resolves; no error


def test_open_question_priority_default():
    assert OpenQuestion(id="Q1", question="?").priority is ConfidenceLevel.MEDIUM
