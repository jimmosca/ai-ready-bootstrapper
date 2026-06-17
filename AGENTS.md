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

Work loop — **Research → Plan → Implement → Verify**, weight on the extremes.
**Compact intentionally**: keep the durable artifacts (research, the plan) on
disk and the working window lean, so you can reset to a fresh context without
losing state. The moves:

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
  Run the suite when something it *executes* changed (code, tests, config it reads
  — **docs and comments don't count**), and once more as the final pre-push gate
  (especially after rebase/squash/reset). **Never re-run a green deterministic
  suite just to recover its output** — capture it the first time.

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

### GitHub workflow

Work in issue-sized **vertical slices**; one **branch + PR per slice**. Defaults
(adopt the repo's own convention if it has one — here we use these): Conventional
Commits, tiny and green; branch `<type>/<issue>-<slug>`; PR `Closes #N`,
**squash-merge**; the Verify gate must pass before merge, and now runs in CI
([`.github/workflows/verify.yml`](.github/workflows/verify.yml)) on every PR and
push to `main`. Minimal labels:
`ready-for-agent`, `needs-info`. Richer machinery (PRD→issues, triage) is
available as skills (`to-prd`, `to-issues`, `triage`) — not mandatory. Why and
the full rules: [ADR-0003](docs/adr/0003-github-working-methodology.md).

Pointers: [`CONTEXT.md`](CONTEXT.md) (language) · [`docs/adr/`](docs/adr/)
(decisions) · §3 below (canonical commands) · the `docs/` contract (listed at
the foot of this file).
<!-- phase0:end -->

## 1. Project purpose

`phase0-bootstrapper` is a **day-zero installer of the living convention
surface**: it carries an unknown/legacy repo to the standard conventions
(`AGENTS.md` + `CONTEXT.md` + `docs/adr/`) via **infer → interview → write**,
and installs an Upkeep Contract so the surface stays current. It is a
**convention bootstrapper for humans and AI alike**, not a documentation
generator and not a context pack compiler.

Parts: the **portable agent skill** (`skills/phase0-bootstrapper/`,
self-contained `SKILL.md` + `resources/`) — the single source; the **Claude
Code skill** (`.claude/skills/phase0-bootstrapper/`), a verbatim mirror of it;
and **`scripts/scan.py`** — the standalone, read-only sensor that emits
structured JSON.

## 2. Non-negotiable principles

- **Read-only target analysis** — writes confined to `AGENTS.md`, `CONTEXT.md`,
  `docs/adr/*`, and `.ai/phase0/scan.json` in the target repo; never touch
  source code, build artefacts, or anything else.
- **Merge via managed markers** — only the
  `<!-- phase0:start -->…<!-- phase0:end -->` block is rewritten; prosa outside
  is never touched.
- **Dry-run / explicit consent** before any write (target-root files are
  high-blast-radius).
- **Evidence-backed claims** — confirmed facts carry an inline `path:line`;
  unconfirmed claims → explicit open question. No `E#` ledger, no
  `evidence-map.md`.
- **No hallucinated architecture** — names are not behavior; prefer "unknown"
  to a confident guess. No invented components, versions, flags, endpoints, ADRs.
- **No source repo modifications during Phase 0** — never edit, run, or install.
- **Lean artifacts, then stop** — MVP scope; day-N upkeep is delegated to the
  installed Upkeep Contract.

Full rules: [`docs/phase0-contract.md`](docs/phase0-contract.md),
[`docs/safety-policy.md`](docs/safety-policy.md),
[`docs/evidence-policy.md`](docs/evidence-policy.md).

## 3. Development commands

Managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                              # create the venv and install deps
uv run pytest                        # tests must pass
uv run ruff check .                  # lint must pass
uv run ruff format .                 # format
python scripts/scan.py <repo-path>   # read-only scan → prints JSON, persists .ai/phase0/scan.json
python scripts/scan.py --no-write <repo-path>  # scan without persisting
```

`scripts/scan.py` is the standalone sensor: read-only, stdlib-only, no LLM.
It emits a structured JSON inventory (languages, file tree, manifests,
detected commands, secret locations, state-detection flags). The only write
is `.ai/phase0/scan.json` in the target repo (skipped with `--no-write`).

## 4. Architecture notes

- **`scripts/scan.py`** — standalone, stdlib-only sensor: read-only inspection
  (path safety, ignored-dir pruning, size-limited reads, project-type /
  important-file / command detection, glossary-candidate extraction,
  state-detection). Emits JSON to stdout and optionally persists
  `.ai/phase0/scan.json`. No package, no pip install required.
- **Skill packaging** — `skills/phase0-bootstrapper/` (portable) is the single
  self-contained source wrapping the three-phase workflow (infer → interview →
  write); `.claude/skills/phase0-bootstrapper/` (Claude Code) is a verbatim
  mirror of it. The canonical sensor is `scripts/scan.py` (used by the tests and
  CI); the skill bundles a localized copy at `resources/scan.py` and runs that.

## 5. Testing expectations

- **Use fixtures** — sample repos in `tests/fixtures/` (`python_fastapi_repo`,
  `node_typescript_repo`, `terraform_repo`, `dbt_repo`, `mixed_data_ai_repo`).
  They are static-analysis input only; they must not require installation.
- **Avoid external services** — no network, no databases.
- **Deterministic tests first** — same input, same output; no time/order flakiness.
- **No LLM calls in tests** — `scripts/scan.py` is deterministic; the
  interview phase is agentic but exercised manually, not in the suite.

## 6. Output quality rules

- **Distinguish epistemics** — tag every claim `[FACT]` / `[INFERENCE]` /
  `[ASSUMPTION]` / `[OPEN]` per [`docs/evidence-policy.md`](docs/evidence-policy.md).
- **Every confirmed claim needs evidence** — a confirmed fact carries an inline
  `path:line`; unconfirmed claims become explicit open questions, not confident
  assertions. Detected commands are `[INFERENCE]` unless found verbatim in a
  manifest, and are never executed.
- **Confidence must be explicit for inferred claims** — low-confidence
  inferences also raise an `[OPEN]`. Output stays lean and gotcha-first.

## 7. Forbidden changes

- **No vector DB.**
- **No external service dependency** (runtime stays Python stdlib only).
- **`scripts/scan.py` must stay deterministic and LLM-free** — the sensor is
  the only path that must be reproducible without an agent. The interview and
  write phases are agentic by design (expected, not forbidden).
- **No destructive commands** on target repos (build/test/install/run/format/
  codegen, git writes, package installs) — see [`docs/safety-policy.md`](docs/safety-policy.md).
- **No broad framework rewrite** — keep changes minimal and contract-driven.

## 8. Review checklist

- [ ] `uv run pytest` passes; `uv run ruff check .` clean — run once as the
      pre-push gate, not repeatedly on docs-only edits (§ "How we work here").
- [ ] Output stays concise (lean, gotcha-first; no filler, no duplication).
- [ ] Safety policy respected — writes confined to `AGENTS.md`, `CONTEXT.md`,
      `docs/adr/*`, `.ai/phase0/scan.json`; merge via managed markers only.
- [ ] Docs updated when the contract changes. `.claude/skills/phase0-bootstrapper/`
      is a **verbatim mirror** of the portable source `skills/phase0-bootstrapper/`
      — regenerate it (`rm -rf .claude/skills/phase0-bootstrapper && cp -r
      skills/phase0-bootstrapper .claude/skills/`), never hand-edit it. The
      portable skill's `resources/{output-schema,safety-policy,evidence-policy}.md`
      and `resources/scan.py` are localized copies of the canonical `docs/`
      versions and `scripts/scan.py`; keep them in sync (a deterministic test
      enforces both — `tests/test_skill_sync.py` (localization rationale in
      ADR-0005)).

## Read these BEFORE making changes

1. [`docs/phase0-contract.md`](docs/phase0-contract.md) — what Phase 0 does /
   doesn't do, input/output contract, three-phase flow, safety model, consumers.
2. [`docs/output-schema.md`](docs/output-schema.md) — artifact shapes and
   skeletons for the living convention surface (`AGENTS.md`, `CONTEXT.md`, ADR).
3. [`docs/safety-policy.md`](docs/safety-policy.md) — allowed vs. forbidden
   operations, write set, managed-marker merge, dry-run/consent gate.
4. [`docs/evidence-policy.md`](docs/evidence-policy.md) — fact / inference /
   assumption / open question, confidence levels, inline `path:line` citations,
   anti-hallucination rules.

Design lineage and rationale: see [`README.md`](README.md).
