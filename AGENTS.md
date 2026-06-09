# AGENTS.md

Guidance for AI coding agents (Codex, Claude, etc.) working in this repository.
Keep it lean: this file routes you to the authoritative contract in
[`docs/`](docs/) instead of duplicating it. Read the relevant doc before editing.

<!-- phase0:start -->
## How we work here

This repo runs on a **living convention surface**: this `AGENTS.md` (routing +
how we work), [`CONTEXT.md`](CONTEXT.md) (shared language), and
[`docs/adr/`](docs/adr/) (durable decisions). Why we adopted it:
[ADR-0001](docs/adr/0001-adopt-living-convention-methodology.md).

Work loop — **Research → Plan → Implement → Verify**, weight on the extremes:

- **Research** (read-only, cheap): read before you write; for a wide sweep,
  delegate to a read-only subagent to protect the main context window.
- **Plan** (proportional to blast radius): non-trivial change → write a plan and
  `grill-me` it first; trivial → go direct. Neither strict SDD-always nor vibe
  coding.
- **Implement**: minimal, surgical diffs; reuse existing patterns and the words
  defined in `CONTEXT.md`.
- **Verify** (hard rule): not done until the canonical commands in §3 pass. Tests
  are the safety net; loop validate → fix → repeat. Framework-agnostic: prefer
  example-based acceptance tests in the repo's existing framework; BDD is not
  imposed ([ADR-0002](docs/adr/0002-no-enforcing-bdd.md)), only run if already present.

### Upkeep Contract

Keep the living convention surface current **in the same change** that makes one
of these true (trigger-driven — most changes trigger nothing):

- A decision that is **hard to reverse, surprising, or carries a real trade-off**
  → an ADR in `docs/adr/`.
- A **new or redefined domain term** → `CONTEXT.md`.
- A change to **how the repo builds / tests / runs / verifies**, or to a
  "Start here" pointer → the relevant line of this file.

If none apply, write nothing. Mechanism by reference to existing skills
(`grill-with-docs`, `to-prd`, `improve-codebase-architecture`); if they aren't
available, write the doc by hand to the same standard.

Pointers: [`CONTEXT.md`](CONTEXT.md) (language) · [`docs/adr/`](docs/adr/)
(decisions) · §3 below (canonical commands) · the `docs/` contract (listed at
the foot of this file).
<!-- phase0:end -->

## 1. Project purpose

`phase0-bootstrapper` performs **read-only repository analysis** and produces
**evidence-based outputs**: it lets a coding agent enter an unknown/legacy repo
**without modifying it** and compile a Phase 0 context pack at the target repo's
`.ai/phase0/` (11 files). It is a **context compiler for coding agents, not a
documentation generator** — the Research artifact a future agent starts from.

Parts: the **Claude Code skill** (`.claude/skills/phase0-bootstrapper/`), a
**portable agent skill** (`skills/phase0-bootstrapper/`, self-contained
`SKILL.md` + `resources/`), and a **Python package + `phase0` CLI**
(`src/phase0_bootstrapper/`).

## 2. Non-negotiable principles

- **Read-only target analysis** — the only write is the target's `.ai/phase0/`.
- **Evidence-backed claims** — every fact cites `path:line` or a read-only
  command, resolving via `evidence-map.md`.
- **No hallucinated architecture** — names are not behavior; prefer "unknown"
  to a confident guess. No invented components, versions, flags, endpoints, ADRs.
- **No source repo modifications during Phase 0** — never edit, run, or install.
- **MVP over framework complexity** — lean artifacts, then stop.

Full rules: [`docs/phase0-contract.md`](docs/phase0-contract.md),
[`docs/safety-policy.md`](docs/safety-policy.md),
[`docs/evidence-policy.md`](docs/evidence-policy.md).

## 3. Development commands

Managed with [`uv`](https://docs.astral.sh/uv/); `src/` layout.

```bash
uv sync                 # create the venv and install deps
uv run pytest           # tests must pass
uv run ruff check .     # lint must pass
uv run ruff format .    # format
uv run phase0 --help    # the CLI
```

`phase0 scan --repo-path R` runs the full read-only pipeline (scan → render →
write) and writes `R/.ai/phase0/`. Flags: `--output-dir`, `--dry-run` (writes
nothing), `--force` (overwrite non-empty output), `--format text|json` (summary
only). The only filesystem write is the output dir.

## 4. Architecture notes

Modules under `src/phase0_bootstrapper/`:

- **`cli.py`** — entrypoint; wires `scan`, prints the concise summary.
- **`scanner.py`** — read-only inspection: path safety, ignored-dir pruning,
  size-limited reads, project-type / important-file / command detection.
- **`renderer.py`** — compiles the scan into a `Phase0Report` and writes the
  11 files (`build_pack` returns the pack without writing; `generate` writes).
- **evaluator** — quality/self-check logic: `Phase0Report.validate()` rejects
  dangling evidence refs; the manifest scorecard records what could not be
  determined. (Currently part of `renderer.py`/`models.py`, not a separate
  module — keep it that way unless a task says otherwise.)
- **`safety.py`** — read-only guardrails: output dir, ignored dirs,
  dangerous-path refusal, read size limit.
- **`models.py`** — data models (`Finding`, `Risk`, `OpenQuestion`,
  `Phase0Report`).
- **Skill packaging** — `skills/phase0-bootstrapper/` (portable) and
  `.claude/skills/phase0-bootstrapper/` (Claude Code) wrap the same workflow.

## 5. Testing expectations

- **Use fixtures** — sample repos in `tests/fixtures/` (`python_fastapi_repo`,
  `node_typescript_repo`, `terraform_repo`, `dbt_repo`, `mixed_data_ai_repo`).
  They are static-analysis input only; they must not require installation.
- **Avoid external services** — no network, no databases.
- **Deterministic tests first** — same input, same output; no time/order flakiness.
- **No LLM calls in tests** (none in the MVP at all — see §7).

## 6. Output quality rules

- **Distinguish epistemics** — tag every claim `[FACT]` / `[INFERENCE]` /
  `[ASSUMPTION]` / `[OPEN]` per [`docs/evidence-policy.md`](docs/evidence-policy.md).
- **Every important claim needs evidence** — a `[FACT]` without an `E#` is a bug;
  downgrade it. Detected commands are `[INFERENCE]` unless found verbatim in a
  manifest, and are never executed.
- **Confidence must be explicit for inferred claims** — low-confidence
  inferences also raise an `[OPEN]`. Output stays lean and gotcha-first.

## 7. Forbidden changes

- **No vector DB.**
- **No external service dependency** (runtime stays Python stdlib only).
- **No LLM integration in the MVP.**
- **No destructive commands** on target repos (build/test/install/run/format/
  codegen, git writes, package installs) — see [`docs/safety-policy.md`](docs/safety-policy.md).
- **No broad framework rewrite** — keep changes minimal and contract-driven.

## 8. Review checklist

- [ ] `uv run pytest` passes; `uv run ruff check .` clean.
- [ ] Output stays concise (lean, gotcha-first; no filler, no duplication).
- [ ] Safety policy respected (read-only; only write is `.ai/phase0/`).
- [ ] Docs updated when the contract changes — keep `docs/`,
      `.claude/skills/phase0-bootstrapper/`, and `skills/phase0-bootstrapper/`
      consistent. The portable skill's
      `resources/{output-schema,safety-policy,evidence-policy}.md` are copies of
      the canonical `docs/` versions; keep them in sync. Bump `schema_version`
      in `manifest.yaml` (template) and `docs/output-schema.md` when the file set
      or sections change.

## Read these BEFORE making changes

1. [`docs/phase0-contract.md`](docs/phase0-contract.md) — what Phase 0 does /
   doesn't do, input/output contract, read-only guarantee, consumers.
2. [`docs/output-schema.md`](docs/output-schema.md) — the 11 output files:
   purpose, required sections, what to exclude, skeletons.
3. [`docs/safety-policy.md`](docs/safety-policy.md) — allowed vs. forbidden
   operations, dangerous commands, handling uncertainty.
4. [`docs/evidence-policy.md`](docs/evidence-policy.md) — fact / inference /
   assumption / open question, confidence levels, evidence format,
   anti-hallucination rules.

Design lineage and rationale: see [`README.md`](README.md).
