---
name: phase0-bootstrapper
description: >-
  Use when entering an unknown, legacy, or unfamiliar repository (software,
  data, or AI/ML) that lacks agent-ready context. Inspects the repo READ-ONLY
  and compiles a lean, evidence-backed Phase 0 context pack under .ai/phase0/
  (repo map, architecture, entrypoints, commands + verification, risks,
  safe-change boundaries, decision log, evidence map, agent handoff) as the
  research foundation for future coding agents. Trigger on "bootstrap this
  repo", "make this repo AI-ready", "generate Phase 0 / a context pack", or
  starting on an unfamiliar/legacy codebase.
---

# Phase 0 Bootstrapper

A **context compiler for coding agents** — not a documentation generator for
humans. It enters an unknown repository, inspects it without changing it, and
compiles the **Research artifact** that every future agent task starts from.

In the Research→Plan→Implement (RPI) loop, this is *Research*. Research errors
are the highest-leverage errors an agent makes, so this pack optimizes for one
thing: a later agent can trust it and act safely.

## Five principles (non-negotiable)

1. **Read-only first.** Never modify existing files. The only write allowed is
   creating the new `.ai/phase0/` directory and its files. No edits, renames,
   installs, formatters, codegen, or `git` writes.
2. **Evidence over vibes.** Every factual claim cites evidence (`path:line`, or
   a read-only command + its output). No evidence → it is not a fact.
3. **Separate epistemics.** Tag everything `[FACT]` / `[INFERENCE]` /
   `[ASSUMPTION]` / `[OPEN]`. Never let an inference pose as a fact.
4. **Lean beats exhaustive.** More context *hurts* a downstream agent
   (Nisi: cutting 95% of skill text raised accuracy 77%→97%). Write **gotcha
   lists, not tutorials.** Capture the non-obvious; omit what the code already
   makes obvious. Every line must earn its place.
5. **MVP, no overengineering.** Produce the eleven artifacts well. Do not build
   tooling, run heavy analysis, or boil the ocean.

## The read-only contract

- ALLOWED: `git status/log/ls-files/blame/show`, `find`, `ls`, Read/`cat`,
  search/`grep`, reading manifests/configs/lockfiles, computing file stats.
- CARE: read `.env.example`/config *schemas*, but NEVER read or copy real secret
  values from `.env`/credential files — record only that they exist + risk.
- FORBIDDEN: editing/creating/deleting any file outside `.ai/phase0/`; running
  build/test/install/run/format commands; any network-mutating action; any
  `git` command that writes; executing scripts from the repo.
- The bootstrapper **documents** how to build/test/run; it does **not run**
  them. Unverified commands are `[INFERENCE]`, never `[FACT]`.
- If unsure whether an action mutates, treat it as forbidden and log an `[OPEN]`.

## Evidence & epistemics convention

Use these tags consistently in every file:

- `[FACT]` — directly observed. MUST include `evidence:` → `path:line` or a
  read-only command + output. Assign an evidence ID (`E1`, `E2`, …).
- `[INFERENCE]` — reasoned from facts. MUST cite supporting evidence IDs +
  `confidence:` `low|medium|high`.
- `[ASSUMPTION]` — unverified but used to proceed. MUST state what would
  confirm/refute it.
- `[OPEN]` — open question for a human or later agent.

Confidence: `high` = multiple independent signals agree; `medium` = one solid
signal; `low` = weak/indirect/convention-based. Prefer "unknown" to a confident
guess. Every evidence ID is collected in `evidence-map.md` for traceability.

## Staying in the smart zone (context discipline)

The bootstrapper must not blow its own context window or it produces sloppy
research. Apply *intentional compaction*:

- For anything but a small repo, **dispatch read-only Explore sub-agents** by
  area (e.g. "map the `services/` tree", "find all entrypoints", "list test &
  CI tooling"). Instruct each to return a **compact summary with `path:line`
  evidence**, not file dumps. Synthesize summaries; don't re-read everything in
  the main context.
- Write each output file as you finish its phase; don't hold all findings in
  context at once.
- Sample breadth-first on huge repos and record the sampling as an
  `[ASSUMPTION]`/`[OPEN]`. Do not attempt exhaustive reading.

## Workflow

Work the phases in order. Each produces file(s) in `.ai/phase0/`. Start every
file from its skeleton in `templates/`. Read `references/output-spec.md` for the
exact per-file contract and `references/inspection-playbook.md` for the signals
to look for by repo type.

**Phase A — Orient & guardrails**
1. Confirm the target repo path; check it's a git repo (note if not).
2. Top-level snapshot: root listing, `git ls-files | wc -l`, language mix.
3. Create `.ai/phase0/`. This is the only directory you create.

**Phase B — Inventory** → `repo-map.md`
4. Structure, languages, key dirs, manifests, lockfiles, file counts, and
   notably large / generated / vendored areas. Cite evidence; stay lean.

**Phase C — Commands & verification loops** → `commands-and-tooling.md`
5. Extract build/test/run/lint/typecheck/format/deploy commands from manifests,
   Makefile, `package.json` scripts, `pyproject.toml`, CI configs, Dockerfiles,
   README. Tag verified-from-source `[FACT]` vs. likely-but-unrun `[INFERENCE]`.
6. Assess the **verification surface** (Reyes): how would an agent *prove* a
   change is correct here? tests + coverage, lint/typecheck, CI gates, and
   **environment reset/setup**. This drives the agent-readiness scorecard.

**Phase D — Entrypoints** → `entrypoints.md`
7. Locate executable entrypoints: CLI mains, server/app bootstraps, HTTP/RPC
   route roots, jobs/workers, cloud/lambda handlers, notebooks, pipeline/DAG
   definitions, training/eval scripts. Cite each `path:line`.

**Phase E — Architecture** → `architecture.md`
8. Infer components, layering, data flow, datastores, external services, and
   boundaries. Tag inferences with confidence. Add a small text/Mermaid diagram
   only if evidence supports it.

**Phase F — Risk & boundaries** → `risk-register.md`, `safe-change-boundaries.md`
9. Risks: secrets/credentials present, missing/sparse tests, unpinned or
   deprecated deps, large binaries, env coupling, dead code, security smells,
   missing CI/verification. Rate likelihood × impact.
10. Boundaries: where change is safe vs. dangerous — generated/vendored code,
    public APIs, migrations, config, and anything lacking verification coverage.

**Phase G — Synthesis**
11. `decision-log.md` — ADR-style (Cichra): each notable decision inferred from
    the code as **what / why / how it's enforced**, evidence-backed. Catalog any
    existing ADRs/PRDs/specs found.
12. `assumptions-and-open-questions.md` — collect every `[ASSUMPTION]`/`[OPEN]`,
    framed as questions a human/agent should resolve (feeds a downstream "grill").
13. `evidence-map.md` — the index of all evidence IDs → `path:line`/command.
14. `agent-handoff.md` — the lean executive summary for the next agent: what
    this repo is, how to safely start, **verified** commands, the
    agent-readiness scorecard, top risks, where to look, and what's unknown.
15. `manifest.yaml` — machine-readable index: schema version, generated-at, repo
    fingerprint, files produced + per-file confidence, readiness scorecard,
    coverage checklist (including what could NOT be determined).

**Phase H — Self-check & finalize**
16. `git status` proves nothing outside `.ai/phase0/` changed. Every `[FACT]`
    has evidence. Every file exists and is non-empty. Fill the manifest checklist
    honestly. Trim anything that doesn't help the next agent.

## Output location

```
<target-repo>/.ai/phase0/
  manifest.yaml          repo-map.md          architecture.md
  entrypoints.md         commands-and-tooling.md
  decision-log.md        assumptions-and-open-questions.md
  risk-register.md       safe-change-boundaries.md
  agent-handoff.md       evidence-map.md
```

## Anti-overengineering guardrails

- Don't run analyzers, build, install deps, or write code in the target repo.
- Prefer a structured list over prose wherever it serves the next agent better.
- Stop when the eleven files are complete, evidence-backed, and self-consistent.
  That is the MVP. Resist the urge to keep documenting.

## References

- `references/output-spec.md` — exact contract for each of the 11 files.
- `references/inspection-playbook.md` — signals by repo type (Node, Python, Go,
  JVM, data/ETL, AI/ML, monorepo, infra) + the agent-readiness scorecard.
- `templates/` — lean starting skeletons for each output file.
