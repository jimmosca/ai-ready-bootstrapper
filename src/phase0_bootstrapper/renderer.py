"""Render the scanner's result into the 11-file Phase 0 pack.

Takes a :class:`~phase0_bootstrapper.scanner.RepoScan`, compiles it into a
:class:`~phase0_bootstrapper.models.Phase0Report` (assigning evidence ids and
deriving conservative risks / assumptions / decisions), and writes the files
defined in ``docs/output-schema.md``.

Discipline (``docs/evidence-policy.md``): every factual claim cites an ``E#``
that resolves in ``evidence-map.md``; inferences carry a confidence level;
uncertainty is stated, never papered over. The only filesystem write is the
target's output directory (``docs/safety-policy.md``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .models import (
    SCHEMA_VERSION,
    ConfidenceLevel,
    Decision,
    Evidence,
    EvidenceKind,
    Finding,
    FindingType,
    OpenQuestion,
    Phase0Report,
    Risk,
    ScanTarget,
)
from .scanner import RepoScan, scan_repo

# The 10 markdown artifacts + manifest.yaml. Order = render/listing order.
MARKDOWN_FILES = (
    "repo-map.md",
    "architecture.md",
    "entrypoints.md",
    "commands-and-tooling.md",
    "decision-log.md",
    "assumptions-and-open-questions.md",
    "risk-register.md",
    "safe-change-boundaries.md",
    "agent-handoff.md",
    "evidence-map.md",
)
ALL_FILES = ("manifest.yaml", *MARKDOWN_FILES)

_NONE = "_none detected (read-only scan)_"
_NL = "\n"


# --- evidence ledger ---------------------------------------------------------


class _Ledger:
    """Assigns one stable ``E#`` per distinct source (evidence-policy.md)."""

    def __init__(self) -> None:
        self.evidence: list[Evidence] = []
        self._by_source: dict[str, str] = {}

    def add(self, claim: str, source: str, kind: EvidenceKind = EvidenceKind.FILE) -> str:
        if source in self._by_source:
            return self._by_source[source]
        eid = f"E{len(self.evidence) + 1}"
        self.evidence.append(Evidence(id=eid, claim=claim, source=source, kind=kind))
        self._by_source[source] = eid
        return eid

    def first(self, paths: list[str], claim: str) -> str:
        return self.add(claim, paths[0])


# --- public API --------------------------------------------------------------


@dataclass
class RenderedPack:
    """Everything a scan produces, before writing: scan, compiled report, files."""

    scan: RepoScan
    report: Phase0Report
    files: dict[str, str]


def _build(scan: RepoScan, generated_at: str | None) -> tuple[Phase0Report, dict[str, str]]:
    """Compile + render. Returns the report and the ``{filename: content}`` map."""
    ts = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ledger = _Ledger()
    report = _compile(scan, ledger, ts)

    files = {
        "repo-map.md": _repo_map(scan, ledger),
        "architecture.md": _architecture(scan, ledger),
        "entrypoints.md": _entrypoints(scan),
        "commands-and-tooling.md": _commands_and_tooling(scan, ledger),
        "decision-log.md": _decision_log(scan, report),
        "assumptions-and-open-questions.md": _assumptions(report),
        "risk-register.md": _risk_register(report),
        "safe-change-boundaries.md": _safe_change(scan),
        "agent-handoff.md": _agent_handoff(scan, report),
        "evidence-map.md": _evidence_map(report),
    }
    files["manifest.yaml"] = _manifest(scan, report, ts)
    report.validate()  # every cited E# must resolve in the evidence map
    return report, files


def build_pack(target: ScanTarget, generated_at: str | None = None) -> RenderedPack:
    """Scan ``target`` read-only and compile+render the pack. Writes nothing."""
    scan = scan_repo(target.repo_path)
    report, files = _build(scan, generated_at)
    return RenderedPack(scan=scan, report=report, files=files)


def render(scan: RepoScan, generated_at: str | None = None) -> dict[str, str]:
    """Produce ``{filename: content}`` for all 11 files (no filesystem writes)."""
    return _build(scan, generated_at)[1]


def generate(target: ScanTarget, generated_at: str | None = None) -> list[Path]:
    """Scan ``target`` read-only, render the pack, and write it. Returns paths written."""
    pack = build_pack(target, generated_at=generated_at)
    return write_pack(target.output_dir, pack.files)


def write_pack(output_dir: Path, files: dict[str, str]) -> list[Path]:
    """Write the pack into ``output_dir`` (the only permitted write)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in ALL_FILES:
        path = output_dir / name
        path.write_text(files[name], encoding="utf-8")
        written.append(path)
    return written


# --- compile: derive evidence-backed report items ----------------------------


def _compile(scan: RepoScan, ledger: _Ledger, ts: str) -> Phase0Report:
    inv = scan.inventory
    imp = scan.important_files
    walk = ledger.add("repository file inventory", "read-only directory walk", EvidenceKind.COMMAND)

    report = Phase0Report(inventory=inv, generated_at=ts, commands=list(scan.commands))
    report.evidence = ledger.evidence  # share the single source of truth

    # Findings: the structured, tagged claims the pack asserts (rendered in
    # repo-map.md). Facts cite the walk; project-type inferences carry confidence.
    findings: list[Finding] = []
    if inv.languages:
        findings.append(
            Finding(
                type=FindingType.FACT,
                statement=f"Languages present: {', '.join(inv.languages)}",
                evidence=[walk],
            )
        )
    _strong_types = {"Python", "Node/TypeScript", "Terraform/IaC", "dbt"}
    for ptype in scan.project_types:
        findings.append(
            Finding(
                type=FindingType.INFERENCE,
                statement=f"Likely project type: {ptype}",
                evidence=[walk],
                confidence=ConfidenceLevel.MEDIUM
                if ptype in _strong_types
                else ConfidenceLevel.LOW,
            )
        )
    report.findings = findings

    # Decisions: only obvious, evidence-backed ones (no invented ADRs).
    decisions: list[Decision] = []
    if "python_manifest" in imp:
        eid = ledger.first(imp["python_manifest"], "Python project manifest")
        decisions.append(
            Decision(
                id="D1",
                decision="Python is a primary language/tooling target",
                why="a Python manifest is present",
                how_enforced=f"manifest at {imp['python_manifest'][0]}",
                confidence=ConfidenceLevel.HIGH,
                evidence=[eid],
            )
        )
    if "node_manifest" in imp:
        eid = ledger.first(imp["node_manifest"], "Node package manifest")
        decisions.append(
            Decision(
                id=f"D{len(decisions) + 1}",
                decision="Node/JS tooling is used (npm scripts)",
                why="package.json is present",
                how_enforced=f"{imp['node_manifest'][0]} scripts",
                confidence=ConfidenceLevel.HIGH,
                evidence=[eid],
            )
        )
    if "dockerfile" in imp:
        eid = ledger.first(imp["dockerfile"], "Dockerfile present")
        decisions.append(
            Decision(
                id=f"D{len(decisions) + 1}",
                decision="Project is packaged as a container image",
                why="a Dockerfile is present",
                how_enforced=imp["dockerfile"][0],
                confidence=ConfidenceLevel.MEDIUM,
                evidence=[eid],
            )
        )
    report.decisions = decisions

    # Risks: concrete, evidence-backed gaps only.
    risks: list[Risk] = []

    def add_risk(risk: str, category: str, likelihood, impact, mitigation: str, eid: str) -> None:
        risks.append(
            Risk(
                id=f"R{len(risks) + 1}",
                risk=risk,
                category=category,
                likelihood=likelihood,
                impact=impact,
                evidence=[eid],
                note=mitigation,
            )
        )

    if "tests" not in imp:
        add_risk(
            "No tests detected in inspected paths",
            "testing-gap",
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.HIGH,
            "Locate or add a test suite before relying on changes; confirm with a maintainer.",
            walk,
        )
    if not scan.commands:
        add_risk(
            "No build/test/run commands detected",
            "verification",
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.HIGH,
            "Ask the maintainer how the project is built and verified.",
            walk,
        )
    if "github_actions" not in imp:
        add_risk(
            "No GitHub Actions CI detected (other CI not inspected)",
            "build-ci",
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.MEDIUM,
            "Confirm whether CI gates exist elsewhere before assuming none.",
            walk,
        )
    report.risks = risks

    # Open questions: the high-value unknowns the scan cannot resolve.
    report.open_questions = [
        OpenQuestion(
            id="Q1",
            question="What is the project's purpose and who owns it?",
            why="purpose/ownership cannot be inferred reliably from structure alone",
            priority=ConfidenceLevel.HIGH,
        ),
        OpenQuestion(
            id="Q2",
            question="How are changes validated before merge (tests/CI)?",
            why="verification surface is the precondition for safe agent work",
            priority=ConfidenceLevel.HIGH,
        ),
        OpenQuestion(
            id="Q3",
            question="What is the primary runtime entrypoint and deployment target?",
            why="entrypoint detection is limited in this read-only MVP",
            priority=ConfidenceLevel.MEDIUM,
        ),
    ]
    return report


# --- per-file renderers ------------------------------------------------------


def _tag(c: ConfidenceLevel | None) -> str:
    return c.value if c is not None else "unknown"


def _md_table(header: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(header) + " |"
    sep = "|" + "|".join(["---"] * len(header)) + "|"
    body = [line, sep]
    body += ["| " + " | ".join(r) + " |" for r in rows]
    if not rows:
        body.append("| " + " | ".join(["—"] * len(header)) + " |")
    return _NL.join(body)


def _overall_confidence(scan: RepoScan) -> str:
    imp = scan.important_files
    signals = sum(
        [bool(scan.project_types), bool(scan.commands), "tests" in imp, "readme" in imp]
    )
    return "medium" if signals >= 3 else "low"


def _manifest(scan: RepoScan, report: Phase0Report, ts: str) -> str:
    inv = scan.inventory
    summaries = {
        "repo-map.md": "languages, layout, important files, project types",
        "architecture.md": "coarse inferred structure (low confidence)",
        "entrypoints.md": "detected commands as entrypoints (not executed)",
        "commands-and-tooling.md": "package manager, tooling, detected commands",
        "decision-log.md": "obvious, evidence-backed decisions only",
        "assumptions-and-open-questions.md": "weak-signal assumptions + open questions",
        "risk-register.md": "concrete gaps with severity/confidence/mitigation",
        "safe-change-boundaries.md": "safe / caution / do-not-touch areas",
        "agent-handoff.md": "operational handoff for the next agent",
        "evidence-map.md": "E# -> source traceability index",
    }
    overall = _overall_confidence(scan)
    lines = [
        f'schema_version: "{SCHEMA_VERSION}"',
        f'phase0_version: "{__version__}"',
        f'generated_at: "{ts}"',
        "generator: phase0-bootstrapper",
        "mode: read-only",
        "repo:",
        f'  name: "{inv.name}"',
        f'  root: "{inv.root}"',
        f"  vcs: {inv.vcs}",
        f'  head_commit: "{inv.head_commit or ""}"',
        f"  file_count: {inv.file_count}",
        f"  languages: [{', '.join(inv.languages)}]",
        f"project_types: [{', '.join(scan.project_types)}]",
        f"analyzed_areas: [{', '.join(scan.top_level)}]",
        f"excluded_areas: [{', '.join(scan.excluded_dirs)}]",
        "files:",
    ]
    for name in MARKDOWN_FILES:
        conf = "low" if name == "architecture.md" else overall
        lines.append(f'  - {{ path: {name}, confidence: {conf}, summary: "{summaries[name]}" }}')
    lines += _agent_readiness_yaml(scan)
    lines += [
        "coverage:",
        f"  inspected: [{', '.join(scan.top_level)}]",
        f"  skipped_or_sampled: [{', '.join(scan.excluded_dirs)}]",
        "  unknown: [runtime behavior, data flow, deployment target]",
        f"overall_confidence: {overall}",
    ]
    return _NL.join(lines) + _NL


def _agent_readiness_yaml(scan: RepoScan) -> list[str]:
    imp = scan.important_files
    cmd_cats = {c.category for c in scan.commands}

    def dim(present: bool, partial: bool = False, note: str = "") -> str:
        status = "present" if present else ("partial" if partial else "absent")
        return f'{{ status: {status}, note: "{note}" }}'

    has_test_cmd = "test" in cmd_cats
    test_partial = "tests" in imp and not has_test_cmd
    return [
        "agent_readiness:",
        f"  build: {dim('build' in cmd_cats or 'dockerfile' in imp)}",
        f"  test: {dim(has_test_cmd or 'tests' in imp, partial=test_partial)}",
        f"  lint_format_typecheck: {dim(bool({'lint', 'format', 'typecheck'} & cmd_cats))}",
        f"  ci_gates: {dim('github_actions' in imp, note='other CI not inspected')}",
        '  env_setup_reset: { status: unknown, note: "not inspected read-only" }',
        f"  run_locally: {dim('run' in cmd_cats)}",
        f"  docs_specs: {dim('readme' in imp)}",
        f"  correctness_signal: {dim('tests' in imp, note='no execution performed')}",
    ]


def _repo_map(scan: RepoScan, ledger: _Ledger) -> str:
    inv = scan.inventory
    imp = scan.important_files
    langs = ", ".join(inv.languages) or "unknown"
    layout = _NL.join(f"- `{name}`" for name in scan.top_level) or _NONE

    rows = []
    for category, paths in imp.items():
        for p in paths:
            rows.append([category, f"`{p}`", ledger.add(f"{category} file", p)])

    if "readme" in imp:
        rid = ledger.first(imp["readme"], "README present")
        purpose = (
            f"See `{imp['readme'][0]}` (evidence {rid}). "
            "`[OPEN]` purpose text not extracted in this MVP."
        )
    else:
        purpose = "`[OPEN]` no README detected; purpose unknown."

    excluded = ", ".join(scan.excluded_dirs) or "none present"
    types = ", ".join(scan.project_types) or "unknown"
    return f"""# Repo Map

## Purpose
{purpose}

## Languages
`[FACT]` {langs} — by file extension over the read-only walk.

## Top-level layout
{layout}

## Important files
{_md_table(["Category", "Path", "Evidence"], rows)}

## Likely project types
`[INFERENCE]` {types} (confidence: low–medium).

## Unclear areas
- Runtime behavior, data flow, and deployment are not inferable from structure alone.
- Excluded from the walk: {excluded}.
"""


def _architecture(scan: RepoScan, ledger: _Ledger) -> str:
    src_like = [n for n in scan.top_level if n in {"src", "lib", "app", "pkg", "internal", "cmd"}]
    rows = []
    for name in src_like:
        rows.append(
            [
                f"`{name}/`",
                "candidate source component",
                "INFERENCE",
                "low",
                ledger.add(f"top-level source dir {name}", name),
            ]
        )
    body = _md_table(["Component", "Responsibility", "Tag", "Confidence", "Evidence"], rows)
    excluded = ", ".join(scan.excluded_dirs) or "none present"
    return f"""# Architecture

> `[INFERENCE]` Structural only. No code-level data-flow or dependency analysis
> was performed (read-only MVP). Names are not behavior.

## Components / modules
{body}

## Layering & data flow
`[OPEN]` Not analyzed in this MVP — requires reading code paths.

## Datastores / external services
`[OPEN]` None asserted; would need `path:line` evidence to claim.

## Confidence & limitations
- Confidence: **low**. Components above are inferred from directory names.
- Excluded from inspection: {excluded}.
- A datastore/integration is only claimed when traceable to a `path:line`.
"""


def _entrypoints(scan: RepoScan) -> str:
    rows = []
    for c in scan.commands:
        if c.category in {"run", "build", "test"}:
            tag = c.finding_type.value.upper()
            rows.append(
                [c.category, f"`{c.command}`", f"`{c.source}`", f"[{tag}] detected, not executed"]
            )
    return f"""# Entrypoints

> Commands below are **detected, not executed** (read-only). Runtime entrypoint
> detection is limited in this MVP — confirm the primary entrypoint manually.

{_md_table(["Type", "Command", "Source", "Status"], rows)}

## Notes
`[OPEN]` The primary application entrypoint was not resolved from structure alone.
"""


def _commands_and_tooling(scan: RepoScan, ledger: _Ledger) -> str:
    imp = scan.important_files
    rows = []
    for c in scan.commands:
        tag = c.finding_type.value
        conf = c.confidence.value if c.confidence else "—"
        eid = ledger.add(f"{c.category} command", c.source)
        rows.append([c.category, f"`{c.command}`", f"`{c.source}`", tag, conf, eid])

    infra = [
        label
        for key, label in (
            ("dockerfile", "Docker"),
            ("docker_compose", "Docker Compose"),
            ("terraform", "Terraform"),
            ("dbt", "dbt"),
            ("github_actions", "GitHub Actions"),
        )
        if key in imp
    ]
    infra_block = (_NL.join(f"- {i}" for i in infra)) if infra else _NONE
    langs = ", ".join(scan.inventory.languages) or "unknown"
    return f"""# Commands & Tooling

> Nothing was executed (read-only). `fact` = found verbatim in a manifest;
> `inference` = inferred from tooling presence (carries confidence).

## Package manager / runtime
- Package manager: {_package_manager(scan)}
- Languages: {langs}

## Detected commands
{_md_table(["Category", "Command", "Source", "Tag", "Confidence", "Evidence"], rows)}

## Infrastructure / CI tools
{infra_block}
"""


def _package_manager(scan: RepoScan) -> str:
    imp = scan.important_files
    parts = []
    if "python_manifest" in imp:
        parts.append("Python (pyproject/pip — `[INFERENCE]` lockfile not inspected)")
    if "node_manifest" in imp:
        parts.append("Node (npm/pnpm/yarn — `[INFERENCE]` lockfile not inspected)")
    return "; ".join(parts) or "unknown"


def _decision_log(scan: RepoScan, report: Phase0Report) -> str:
    blocks = []
    for d in report.decisions:
        blocks.append(
            f"### {d.id} — {d.decision}\n"
            f"- Why (inferred): {d.why}\n"
            f"- How enforced: {d.how_enforced}\n"
            f"- Confidence: {d.confidence.value}\n"
            f"- Evidence: {', '.join(d.evidence)}"
        )
    decisions = "\n\n".join(blocks) or "_No decisions could be inferred with evidence._"
    adr_rows = [[f"`{p}`", "decision record", "found"] for p in scan.important_files.get("adr", [])]
    return f"""# Decision Log (ADR-style)

> Only decisions directly backed by evidence. No ADRs are invented.

{decisions}

## Existing decision artifacts found
{_md_table(["Doc", "Topic", "Status"], adr_rows)}
"""


def _assumptions(report: Phase0Report) -> str:
    inv = report.inventory
    a_rows = []
    if inv and inv.languages:
        a_rows.append(
            [
                "A1",
                f"Primary language is {inv.languages[0]}",
                "confirm via maintainer / manifest",
                "medium",
            ]
        )
    a_rows.append(
        [
            "A2",
            "The inspected tree is representative (no large excluded source areas)",
            "confirm excluded dirs are vendored/generated only",
            "medium",
        ]
    )
    q_rows = [[q.id, q.question, q.why, q.priority.value] for q in report.open_questions]
    return f"""# Assumptions & Open Questions

> Assumptions come from weak/incomplete signals — verify before relying on them.

## Assumptions
{_md_table(["A#", "Assumption", "Confirm / refute by", "Impact"], a_rows)}

## Open questions
{_md_table(["Q#", "Question", "Why it matters", "Priority"], q_rows)}

## Suggested questions to grill a maintainer
- How do I build, run, and test this locally? What resets the environment?
- Which areas are safe to change vs. landmine territory?
- Where does configuration / secrets come from in each environment?
"""


def _risk_register(report: Phase0Report) -> str:
    rows = []
    for r in report.risks:
        rows.append(
            [
                r.id,
                r.risk,
                r.category,
                r.impact.value,  # severity
                r.likelihood.value,  # confidence the risk applies
                ", ".join(r.evidence),
                r.note,  # mitigation
            ]
        )
    top = _NL.join(f"{i + 1}. {r.id} — {r.risk}" for i, r in enumerate(report.risks[:3])) or "—"
    table = _md_table(
        ["ID", "Risk", "Category", "Severity", "Confidence", "Evidence", "Mitigation"], rows
    )
    return f"""# Risk Register

> Concrete, evidence-backed gaps only. Severity = impact; Confidence = how sure
> the risk applies given a read-only scan.

{table}

## Top 3 risks for the next agent
{top}
"""


def _safe_change(scan: RepoScan) -> str:
    imp = scan.important_files
    safe_rows = []
    if "tests" in imp:
        safe_rows.append(["test files", "changes are guarded by existing tests", imp["tests"][0]])
    if "readme" in imp:
        safe_rows.append(["docs / README", "documentation, low blast radius", imp["readme"][0]])

    caution_rows = []
    for key, why in (
        ("python_manifest", "dependency/build config — affects whole project"),
        ("node_manifest", "dependency/build config — affects whole project"),
        ("docker_compose", "runtime topology — affects how services start"),
        ("terraform", "infrastructure — changes can affect live resources"),
    ):
        if key in imp:
            caution_rows.append([f"`{imp[key][0]}`", why, imp[key][0]])

    excluded = ", ".join(scan.excluded_dirs) or "none present"
    dnt = (
        f"- excluded/vendored/build dirs: {excluded}\n"
        "- lockfiles and generated files (not hand-edited)"
    )
    return f"""# Safe-Change Boundaries

> Based on scanner signals. When a boundary is unclear, treat it as caution.

## Safe to change
{_md_table(["Area", "Why safe", "Evidence"], safe_rows)}

## Caution — ask / plan first
{_md_table(["Area", "Why dangerous", "Evidence"], caution_rows)}

## Do-not-touch
{dnt}
"""


def _agent_handoff(scan: RepoScan, report: Phase0Report) -> str:
    inv = scan.inventory
    facts = [c for c in scan.commands if c.finding_type is FindingType.FACT]
    infers = [c for c in scan.commands if c.finding_type is FindingType.INFERENCE]
    fact_lines = _NL.join(f"- `{c.command}`  ({c.source})" for c in facts) or "_none_"
    infer_lines = (
        _NL.join(f"- `{c.command}`  (inferred, {_tag(c.confidence)})" for c in infers) or "_none_"
    )
    top_risks = _NL.join(f"- {r.risk}" for r in report.risks[:3]) or "- none recorded"
    open_qs = _NL.join(f"- {q.question}" for q in report.open_questions) or "- none"
    stack = ", ".join(scan.project_types) or "unknown stack"
    langs = ", ".join(inv.languages) or "unknown"
    return f"""# Agent Handoff

## What this repo is
{inv.name} — {stack}; languages: {langs}.

## Start here
1. `manifest.yaml` for the machine-readable index + readiness.
2. `repo-map.md` and `commands-and-tooling.md`.
3. `risk-register.md` and `assumptions-and-open-questions.md` before editing.

## Commands (detected, NOT executed)
Nothing was run — this is a read-only pack.

**Found in manifests (`[FACT]`):**
{fact_lines}

**Inferred (`[INFERENCE]`, verify before trusting):**
{infer_lines}

## Top risks
{top_risks}

## Safe-change rules
- See `safe-change-boundaries.md`. Avoid manifests/lockfiles/infra without a plan.

## Biggest unknowns
{open_qs}

## Suggested next step (Research → Plan → Implement)
Resolve the open questions (esp. how changes are verified) before planning any
implementation. Do not start Implement until a verification loop is confirmed.
"""


def _evidence_map(report: Phase0Report) -> str:
    header = "| ID | Claim (short) | Source (path:line or command) | Type |"
    sep = "|---|---|---|---|"
    rows = [e.as_row() for e in report.evidence] or ["| — | — | — | — |"]
    return "# Evidence Map\n\n" + _NL.join([header, sep, *rows]) + _NL
