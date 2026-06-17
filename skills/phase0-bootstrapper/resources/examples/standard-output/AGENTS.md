# AGENTS.md

Guidance for AI coding agents and human maintainers working in this repository.
Keep it lean: this file routes you to the authoritative sources instead of
duplicating them.

<!-- phase0:start -->
## What this repo is

`<repo-name>` — <2–3 line description of what this repo does and for whom>.

## Canonical commands

```bash
<build-command>     # build / install
<test-command>      # run tests
<lint-command>      # lint / typecheck
<run-command>       # run locally
```

<!-- If no verification loop was found by the scan, replace the block above with:
No automated verification found; high-risk changes; verify manually by <X>.
Setting up verification is the first recommended task. -->

## How we work here

Work loop — **Research → Plan → Implement → Verify**, weight on the extremes.
**Compact intentionally**: keep the durable artifacts (research, the plan) on
disk and the working window lean, so you can reset to a fresh context without
losing state. The moves:

- **Research** (read-only, cheap): read before you write; for a wide sweep,
  delegate to a read-only subagent to protect the main context window.
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
- A change to **how the repo builds / tests / runs / verifies**, or to a
  "Start here" pointer → the relevant line of this file.

If none apply, write nothing. Mechanism by reference: `grill-with-docs`,
`to-prd`, `improve-codebase-architecture`.

## Start here

- `<path/to/entrypoint>` — <what it is>
- `<path/to/key-config>` — <what it is>

## Pointers

[`CONTEXT.md`](CONTEXT.md) (language) · [`docs/adr/`](docs/adr/) (decisions)
<!-- phase0:end -->
