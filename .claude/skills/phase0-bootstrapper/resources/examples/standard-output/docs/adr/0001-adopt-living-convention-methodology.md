# 0001 — Adopt the living-convention methodology

- **Status:** Accepted
- **Date:** YYYY-MM-DD

## Context

This repo lacked a shared convention surface — no `AGENTS.md`, no shared
glossary, no durable decision record. Different agents and maintainers were
reaching different conclusions about the same parts of the codebase. The research
phase before any non-trivial change was being redone from scratch every time.

The phase0-bootstrapper installed a small, standard surface: `AGENTS.md` +
`CONTEXT.md` + `docs/adr/`, governed by an Upkeep Contract. This ADR records
why we adopted that convention.

## Decision

Adopt the **living convention surface** — `AGENTS.md` (routing + how we work),
`CONTEXT.md` (shared language), `docs/adr/` (durable decisions) — as this repo's
agent-facing convention, governed by:

- the **RPI+Verify loop** with weight on the extremes, with **Verify as a hard
  rule** (a change is not done until the canonical commands pass), and
- an **Upkeep Contract** in `AGENTS.md` that keeps the surface current in the
  same change that triggers it.

The operative detail is not repeated here: the loop and the Upkeep Contract live
in [`../../AGENTS.md`](../../AGENTS.md); the vocabulary lives in
[`../../CONTEXT.md`](../../CONTEXT.md). This ADR records only the choice and the why.

## Why this is an ADR

It meets all three ADR triggers: it is **hard to reverse** (it reshapes how
agents and maintainers orient to this repo), **surprising without context** (the
choice of this specific surface over other documentation styles is not obvious),
and carries a **real trade-off** (ecosystem alignment and a maintainable surface,
at the cost of any bespoke documentation system already in place).

## Consequences

- The deliverable is the standard surface, merged into the repo's existing files
  via managed markers — not a fresh bespoke tree.
- Day-zero installs the surface and stops; day-N upkeep is delegated to ecosystem
  skills (`grill-with-docs`, `to-prd`, `improve-codebase-architecture`).
- Future agents read `AGENTS.md` first, then `CONTEXT.md` and `docs/adr/` as
  needed. Humans validate and answer open questions; agents act safely from it.
