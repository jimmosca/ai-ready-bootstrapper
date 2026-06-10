---
name: phase0-bootstrapper
description: >-
  Use when entering an unknown, legacy, or unfamiliar repository that lacks a
  living convention surface (AGENTS.md / CONTEXT.md / docs/adr/). Installs the
  surface via infer → interview → write and seeds an Upkeep Contract so it stays
  current. Trigger on "bootstrap this repo", "make this repo AI-ready", or before
  starting work in an unfamiliar codebase.
---

# Phase 0 Bootstrapper

A **day-zero installer for humans and agents alike** — not a documentation
generator. It enters an unknown repo, inspects it without changing it, and
installs the **living convention surface** (`AGENTS.md` + `CONTEXT.md` +
`docs/adr/`) via **infer → interview → write**, then stops.

## When to use

- The target repo lacks `AGENTS.md`, `CONTEXT.md`, or `docs/adr/`.
- You need ground truth before planning a change in an unfamiliar area.
- The user says "bootstrap this repo", "make this codebase AI-ready", or
  "generate a Phase 0 / context pack".

## When NOT to use

- The repo is **already bootstrapped** (healthy `CONTEXT.md` + ADRs + Upkeep
  Contract present) — decline and offer a top-up instead.
- The task is to change code — that is Plan / Implement, not Phase 0.
- The path is a system/home root or does not exist.

## Flow

### 0. Detect state
Run `python scripts/scan.py <path> --no-write` and read `.state`:
- **virgin** → full install.
- **partial** → merge; do not recreate what already exists.
- **already-bootstrapped** → decline; offer to add the Upkeep Contract if missing.

### 1. Infer (read-only)
Run `python scripts/scan.py <path>`. Builds `scan.json` with facts, glossary
candidates, and the state hint. Build an internal draft: facts (`path:line`),
inferences (with confidence), open questions. Write nothing yet.

### 2. Interview
Surface open questions and low-confidence inferences to the maintainer. Answers
promote inferences → facts and crystallise decisions (→ ADR) and terms (→
`CONTEXT.md`). Gate style: `grill-me`. If running `--no-interview`, skip to §3
and mark all unconfirmed items `[OPEN]`.

### 3. Write (lazy, merged, consented)
Preview proposed writes; wait for **explicit consent** before writing. Then:
- **`AGENTS.md`** — 6-section skeleton (see `templates/AGENTS.md`); merged into
  managed markers `<!-- phase0:start -->…<!-- phase0:end -->`; always written.
- **`CONTEXT.md`** — **lazy**: only if the interview confirms real domain terms
  (use `templates/CONTEXT.md`).
- **`docs/adr/`** — **lazy**: only confirmed, hard-to-reverse decisions; ADR-0001
  (methodology) always written — the bootstrapper dogfoods its first act
  (use `templates/adr.md`).
- **`.ai/phase0/scan.json`** — sensor output; written without a consent prompt.

Re-running replaces only the managed block (**idempotent**).

### Degradation (`--no-interview`)
**Always write:** `AGENTS.md` skeleton + "How we work" + Upkeep Contract + ADR-0001.
**Skip:** `CONTEXT.md`, repo-specific ADRs.
Mark unconfirmed items as "Open questions for a maintainer".

## Allowed actions

Read files, list dirs, grep, read-only `git` commands. Write set:
`AGENTS.md`, `CONTEXT.md`, `docs/adr/*`, `.ai/phase0/scan.json`.

## Forbidden actions

- Editing / creating / deleting anything outside the write set.
- Running build / test / install / run / lint / codegen; any `git` write;
  package-manager installs; network mutations.
- Reading or copying secret values — note existence + location only.
- If unsure whether an action mutates state → don't; log an `[OPEN]`.

## After writing

Point the maintainer at `AGENTS.md`. Day-N upkeep delegates to ecosystem skills:
`grill-with-docs`, `to-prd`, `improve-codebase-architecture`.

## References

- `docs/phase0-contract.md` — the formal contract (what / what not / state / degradation).
- `docs/output-schema.md` — artifact shapes, skeletons, managed-marker merge.
- `docs/safety-policy.md` — full write set, forbidden commands, consent rules.
- `docs/evidence-policy.md` — the four epistemic tags; citation format.
- `templates/` — lean skeletons: `AGENTS.md`, `CONTEXT.md`, `adr.md`.
- `scripts/scan.py` — the read-only sensor.
