# 0007 — Route foreign agent entrypoints to `AGENTS.md`

- **Status:** Accepted
- **Date:** 2026-06-17

## Context

The bootstrapper installs `AGENTS.md` as the **canonical** entrypoint
([ADR-0001](0001-adopt-living-convention-methodology.md)). But agents disagree on
which file they read first: Claude Code reads `CLAUDE.md`, GitHub Copilot reads
`.github/copilot-instructions.md`. A repo bootstrapped to `AGENTS.md` is therefore
invisible to an agent that only consults its own native entrypoint — the surface is
installed but not reached.

The skill already half-addressed this for Claude: the safety policy said "if
`CLAUDE.md` exists, ensure it routes to `AGENTS.md`", yet `CLAUDE.md` was **not** in
the write set — an inconsistency (a write the policy permitted but the write set
didn't list). Nothing covered Copilot at all. The sensor observed `claude_md` but
not `copilot_instructions`, so the write phase had no honest signal to act on.

## Decision

Treat present **foreign agent entrypoints** as a bounded, pointer-only extension of
the write set:

- The sensor (`scripts/scan.py` / `resources/scan.py`) emits a new presence boolean
  `state.signals.copilot_instructions` (`.github/copilot-instructions.md` exists),
  alongside the existing `claude_md`. The `status` formula is unchanged — a foreign
  entrypoint is not the canonical surface, so it does not flip `virgin`.
- The write set gains `CLAUDE.md` and `.github/copilot-instructions.md`, **pointer
  only**: for each entrypoint that **already exists**, the write phase inserts (or
  refreshes) a managed-marker block `<!-- phase0:start -->…<!-- phase0:end -->`
  routing to `AGENTS.md`. Human-authored prose outside the markers is never touched;
  a missing entrypoint is **not** created.
- These are surface-facing edits, so — unlike the internal `scan.json` / `draft.md`
  — they go through the **dry-run preview + explicit consent** like `AGENTS.md`.

## Why this is an ADR

It expands the write set, which the contract says must never grow "without an ADR",
and it resolves a standing inconsistency (the `CLAUDE.md` routing rule that the
write set didn't list). A future reader needs to know the expansion is deliberately
bounded — a pointer to the single canonical file, never a second copy of the
guidance — so it does **not** breach "no parallel taxonomy": there is still exactly
one surface, with thin routes into it.

**Considered and deferred (non-goal):** *creating* a foreign entrypoint when absent
(e.g. seeding `.github/copilot-instructions.md` on a virgin repo so every
bootstrapped repo is Copilot-reachable). That makes the bootstrapper author a file
in a foreign agent's namespace, a larger surface decision; for now we only route
entrypoints the repo already owns. Revisit if reachability-on-virgin proves needed.

## Consequences

- A bootstrapped repo is reachable by both Claude and Copilot when those entrypoints
  are present — the surface is not just installed but actually loaded.
- The `CLAUDE.md` write-set ambiguity is resolved: it is now a listed, pointer-only
  member of the write set with the same consent gate as the rest of the surface.
- The sensor stays deterministic and stdlib-only; the new signal is one `is_file()`
  check. The write-phase routing itself is agentic (not unit-tested); the testable
  part is the sensor detection, which a fixture-based test locks.
- A virgin repo with no foreign entrypoint is unaffected — nothing is created.
