# AGENTS.md
<!-- phase0:start -->
## What this repo is
<!-- 2–3 lines: what this repo does and for whom. No marketing prose. -->

## Canonical commands
<!-- Copy-pasteable build / test / lint / run / verify. If the scan found none,
say so explicitly: "no automated verification found; high-risk changes; verify
manually via [X]; setting up verification is the first recommended task." -->

## How we work here
<!-- The RPI+Verify loop in ~5 bullets, weight on the extremes.
Name the skills used (grill-me / tdd / grill-with-docs). -->
- **Research** (read-only, cheap): read before you write; delegate wide sweeps
  to a read-only subagent to protect the main context window.
- **Plan** (proportional to blast radius): non-trivial change → write a plan and
  `grill-me` it first; trivial → go direct.
- **Implement**: minimal, surgical diffs; reuse existing patterns and the words
  defined in `CONTEXT.md`.
- **Verify** (hard rule): not done until the canonical commands above pass. Tests
  are the safety net; loop validate → fix → repeat.

### Upkeep Contract
Keep the living convention surface current **in the same change** that makes one
of these true (trigger-driven — most changes trigger nothing):

- A decision that is **hard to reverse, surprising, or carries a real trade-off**
  → an ADR in `docs/adr/`.
- A **new or redefined domain term** → `CONTEXT.md`.
- A change to **how the repo builds / tests / runs / verifies**, or to a "Start
  here" pointer → the relevant line of this file.

If none apply, write nothing. Mechanism by reference: `grill-with-docs`,
`to-prd`, `improve-codebase-architecture`.

## Start here
<!-- Pointers into the repo — where to begin reading. Not copies. -->

## Pointers
[`CONTEXT.md`](CONTEXT.md) (language) · [`docs/adr/`](docs/adr/) (decisions)
<!-- phase0:end -->
