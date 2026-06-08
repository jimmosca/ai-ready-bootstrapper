"""Data models for the Phase 0 context pack.

Small, explicit dataclasses (standard library only) that map to the outputs in
``docs/output-schema.md`` and enforce the discipline in ``docs/evidence-policy.md``:

- every claim has an epistemic ``FindingType`` (fact / inference / assumption / open);
- a ``FACT`` must carry evidence; an ``INFERENCE`` must carry a ``ConfidenceLevel``;
- evidence is referenced by id and resolved in one place (``Phase0Report.evidence``).

Deliberately minimal: no ORM, no graph/vector store, no LLM plumbing. Add fields
when an output needs them, not before.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

#: Output contract version recorded in manifest.yaml.
SCHEMA_VERSION = "0.1"


class FindingType(str, Enum):
    """The four epistemic tags (evidence-policy.md)."""

    FACT = "fact"
    INFERENCE = "inference"
    ASSUMPTION = "assumption"
    OPEN = "open"


class ConfidenceLevel(str, Enum):
    """Three-point scale, reused for inference confidence and risk likelihood/impact."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceKind(str, Enum):
    """Where a piece of evidence comes from (evidence-map.md ``type`` column)."""

    FILE = "file"
    COMMAND = "command"
    CONFIG = "config"


@dataclass(frozen=True)
class ScanTarget:
    """A repository to inspect and where to write its Phase 0 pack."""

    repo_path: Path
    output_dir: Path


@dataclass(frozen=True)
class Evidence:
    """A single, citable source. Resolves an ``E#`` id used elsewhere."""

    id: str  # e.g. "E1"
    claim: str  # short description of what this evidences
    source: str  # "path:line" or a read-only command
    kind: EvidenceKind = EvidenceKind.FILE

    def as_row(self) -> str:
        """Render the evidence-map.md table row."""
        return f"| {self.id} | {self.claim} | {self.source} | {self.kind.value} |"


@dataclass
class Finding:
    """A tagged claim. The core unit; everything else can reference evidence too."""

    type: FindingType
    statement: str
    evidence: list[str] = field(default_factory=list)  # Evidence ids
    confidence: ConfidenceLevel | None = None
    # Assumption-only context (output-schema.md: confirm/refute, impact if wrong).
    confirm_refute: str | None = None
    impact_if_wrong: ConfidenceLevel | None = None

    def __post_init__(self) -> None:
        if self.type is FindingType.FACT and not self.evidence:
            raise ValueError("a FACT must cite at least one evidence id")
        if self.type is FindingType.INFERENCE and self.confidence is None:
            raise ValueError("an INFERENCE must carry a confidence level")


@dataclass
class RepoInventory:
    """The ``repo`` block of manifest.yaml + basis for repo-map.md."""

    name: str
    root: str
    vcs: str = "git"  # or "none"
    head_commit: str | None = None
    file_count: int = 0
    languages: list[str] = field(default_factory=list)


@dataclass
class CommandInfo:
    """A build/test/run/verify command (commands-and-tooling.md).

    Found in source => ``FACT`` (``source`` is its path:line). Not run / inferred
    => ``INFERENCE`` and must carry confidence.
    """

    category: str  # build | test | lint | typecheck | format | run | deploy
    command: str
    source: str  # path:line where the command was found
    finding_type: FindingType = FindingType.FACT
    confidence: ConfidenceLevel | None = None
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.finding_type is FindingType.INFERENCE and self.confidence is None:
            raise ValueError("an inferred (unrun) command must carry confidence")


@dataclass
class Entrypoint:
    """An executable entrypoint (entrypoints.md)."""

    path: str
    kind: str  # cli | server | route | worker | job | handler | notebook | dag | training
    description: str = ""
    trigger: str = ""
    line: int | None = None
    evidence: list[str] = field(default_factory=list)

    @property
    def location(self) -> str:
        """``path:line`` when a line is known, else just ``path``."""
        return f"{self.path}:{self.line}" if self.line is not None else self.path


@dataclass
class Decision:
    """ADR-style inferred decision (decision-log.md): what / why / how enforced.

    ``why`` is always inferred, so a confidence level is always carried.
    """

    id: str  # e.g. "D1"
    decision: str
    why: str
    how_enforced: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    evidence: list[str] = field(default_factory=list)


@dataclass
class Risk:
    """A ranked risk (risk-register.md)."""

    id: str  # e.g. "R1"
    risk: str
    category: str  # security | testing-gap | dependency | build-ci | data | ...
    likelihood: ConfidenceLevel
    impact: ConfidenceLevel
    evidence: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class OpenQuestion:
    """An unresolved question for a human/agent (assumptions-and-open-questions.md)."""

    id: str  # e.g. "Q1"
    question: str
    why: str = ""
    priority: ConfidenceLevel = ConfidenceLevel.MEDIUM


@dataclass
class Phase0Report:
    """In-memory aggregate of everything the scanner gathers.

    The renderer turns this into the 11 ``.ai/phase0/`` files. ``evidence`` is the
    single source of truth for ``E#`` ids; ``validate()`` checks every reference
    resolves (the traceability guarantee from phase0-contract.md).
    """

    inventory: RepoInventory | None = None
    schema_version: str = SCHEMA_VERSION
    generator: str = "phase0-bootstrapper"
    generated_at: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    commands: list[CommandInfo] = field(default_factory=list)
    entrypoints: list[Entrypoint] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    open_questions: list[OpenQuestion] = field(default_factory=list)

    def evidence_ids(self) -> set[str]:
        """Ids defined in the evidence map."""
        return {e.id for e in self.evidence}

    def referenced_evidence_ids(self) -> set[str]:
        """Ids cited by any finding/command/entrypoint/decision/risk."""
        refs: set[str] = set()
        carriers = (*self.findings, *self.commands, *self.entrypoints, *self.decisions, *self.risks)
        for item in carriers:
            refs.update(item.evidence)
        return refs

    def unresolved_evidence_refs(self) -> set[str]:
        """Cited ids that are not defined in the evidence map."""
        return self.referenced_evidence_ids() - self.evidence_ids()

    def validate(self) -> None:
        """Raise if any cited evidence id is undefined."""
        missing = self.unresolved_evidence_refs()
        if missing:
            raise ValueError(f"evidence ids referenced but not defined: {sorted(missing)}")

    def findings_by_type(self, finding_type: FindingType) -> list[Finding]:
        return [f for f in self.findings if f.type is finding_type]
