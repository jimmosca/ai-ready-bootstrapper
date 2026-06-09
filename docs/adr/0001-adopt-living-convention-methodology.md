# 0001 — Adopt the living-convention methodology

- **Status:** Accepted
- **Date:** 2026-06-09

## Context

This repo's job is to make unknown repos agent-ready. The original design did
that by emitting a bespoke 11-file pack under `.ai/phase0/` — its own taxonomy
(`repo-map.md`, `architecture.md`, `evidence-map.md`, `manifest.yaml`, …). That
created a parallel system the wider ecosystem doesn't speak, and it only
inferred (read-only, no interview), so half the knowledge a maintainer holds
never made it in.

The practitioners we benchmark against converged on a small, standard surface
instead: `AGENTS.md` + `CONTEXT.md` + `docs/adr/`, kept alive as code changes.
We want this repo to live by the same convention it will install in others
(dogfooding), and the methodology must be **installed, not just described** —
written into the surface so future agents follow it without being told.

## Decision

Adopt the **living convention surface** — `AGENTS.md` (routing + how we work),
`CONTEXT.md` (shared language), `docs/adr/` (durable decisions) — as this repo's
agent-facing convention, governed by:

- the **RPI+Verify loop** with weight on the extremes, with **Verify as a hard
  rule** (a change is not done until the canonical commands pass), and
- an **Upkeep Contract** in `AGENTS.md` that keeps the surface current in the
  same change that triggers it.

The operative detail is not repeated here: the loop and the Upkeep Contract live
in [`AGENTS.md`](../../AGENTS.md); the vocabulary lives in
[`CONTEXT.md`](../../CONTEXT.md). This ADR records only the choice and the why.

## Why this is an ADR

It meets all three of our ADR triggers: it is **hard to reverse** (it reshapes
the whole deliverable), **surprising without context** (it retires the
`.ai/phase0/` pack this repo was built to produce), and carries a **real
trade-off** (ecosystem alignment and a maintainable surface, bought at the cost
of a bespoke artifact set we already had).

## Consequences

- The deliverable is the standard surface, merged into a repo's existing files
  via managed markers — not a fresh bespoke tree.
- Day-zero installs the surface and stops; day-N upkeep is delegated to ecosystem
  skills (`grill-with-docs`, `to-prd`, `improve-codebase-architecture`).
- The bespoke 11-file schema, the product CLI, and the `renderer`/`models` code
  are superseded; their removal is a separate, later change (this ADR predates
  the code pivot).
- Where a repo has no verification loop, that absence becomes the #1 open
  question rather than a silently dropped rule.

## References

The methodology distills seven sources: Anthropic (Claude Code best practices /
Building Effective Agents), Matt Pocock (`AGENTS.md` / `CONTEXT.md` / `docs/adr/`
convention, [`mattpocock/skills`](https://github.com/mattpocock/skills)), Andrej
Karpathy (surgical changes, verifiable success criteria), Spec-Driven
Development, [ai.engineer](https://www.ai.engineer/) (reliability over autonomy),
[goodailist.com](https://goodailist.com/) (adopt what works), and 2026
state-of-the-practice write-ups. See also the design lineage in
[`README.md`](../../README.md).
