# Output spec — the 11 Phase 0 files

The contract for each artifact in `.ai/phase0/`. Keep every file **lean and
gotcha-first** (Nisi): capture the non-obvious, omit what the code already makes
obvious. Every factual claim carries an evidence ID (`E#`) resolved in
`evidence-map.md`. Use the `[FACT]/[INFERENCE]/[ASSUMPTION]/[OPEN]` tags.

Start each file from its skeleton in `templates/`.

---

## manifest.yaml  (machine-readable index — read this first, programmatically)
- `schema_version`, `generated_at` (ISO-8601), `generator: phase0-bootstrapper`.
- `repo`: name, root, vcs, `head_commit`, `file_count`, primary languages.
- `files`: list of the 10 markdown artifacts with `path` + `confidence`
  (`low|medium|high`) + one-line `summary`.
- `agent_readiness`: the scorecard (see inspection-playbook) — per-dimension
  `status` (`present|partial|absent|unknown`) + note.
- `coverage`: checklist of what was inspected vs. skipped/unknown, honestly.
- It must be valid YAML and parseable without the prose files.

## repo-map.md
- Languages + rough proportions; top-level layout (annotated tree, not a full
  dump); key directories and their purpose; manifests & lockfiles; build outputs,
  vendored, and generated areas; notably large files. Evidence per claim.

## commands-and-tooling.md
- Tables for build / test / lint / typecheck / run / deploy. Each row: command,
  source (`path:line`), `[FACT]` (found in source) vs `[INFERENCE]` (not run).
- **Verification surface** (Reyes): how an agent proves a change is correct —
  test framework & how to run a single test, coverage, lint/format/typecheck,
  CI gates, and **environment setup/reset** (Docker, devcontainer, fixtures,
  seed data). Flag missing loops as risks.

## entrypoints.md
- Every executable entrypoint with `path:line`, type (CLI/server/route/worker/
  job/handler/notebook/DAG/training), trigger, and a one-line "what it does".
  Group by type. This is the "where do I start reading" map.

## architecture.md
- Components/modules and responsibilities; layering; data flow; datastores;
  external services/integrations; key cross-cutting concerns (auth, config,
  logging). Inferences tagged with confidence. Optional small Mermaid diagram
  only if evidence supports it. No speculation presented as fact.

## risk-register.md
- Table: `id | risk | category | evidence | likelihood | impact | note`.
  Categories: security/secrets, testing-gap, dependency, build/CI, data, perf,
  maintainability, agent-readiness. Sort by impact. Secrets: record existence
  and location only — never the value.

## safe-change-boundaries.md
- **Safe to change** (well-tested, isolated) and **Dangerous / ask first**
  (public APIs, migrations, generated/vendored code, config, untested hot paths).
  Each with evidence and the reason. This is the guardrail for the next agent.

## decision-log.md  (ADR-style — Cichra)
- Each decision inferred from the code: **Decision · Why (inferred) · How it's
  enforced** (lint rule, CI check, type, convention) · evidence · confidence.
- Also catalog **existing** ADRs/PRDs/specs/design docs found (path + topic).

## assumptions-and-open-questions.md
- All `[ASSUMPTION]`s (with what would confirm/refute) and all `[OPEN]`
  questions, prioritized. Phrase them so a human or a "grill-me" session can
  resolve them directly. These are the highest-value unknowns.

## evidence-map.md
- The traceability index: `E# | claim (short) | path:line or command | type`.
  Every `[FACT]` across all files resolves here. Single source of truth.

## agent-handoff.md  (the entrypoint for the next agent — write last)
- Lean executive summary. Sections: **What this repo is** (2–3 lines) ·
  **Start here** (key files/dirs) · **Verified commands** (only `[FACT]` ones) ·
  **Agent-readiness scorecard** · **Top risks** · **Safe-change rules** ·
  **Biggest unknowns** · **Suggested next step** (RPI: do Research→Plan before
  Implement; point at the relevant files).
- **Reference the other 10 files by path; do NOT duplicate their content.**
- Redact any secrets/PII. If something is unknown, say so plainly.
