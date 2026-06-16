# 0004 — Mirror the Claude Code skill verbatim from the portable source

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

The bootstrapper ships in two skill trees: `skills/phase0-bootstrapper/` (the
portable, self-contained skill for any agent) and
`.claude/skills/phase0-bootstrapper/` (the one Claude Code auto-discovers in this
repo). They had diverged — different sensor paths and different skeleton
strategies — and were reconciled by hand via the AGENTS.md §8 checklist. The
README's global-install line copied the `.claude/` tree, which was **broken**:
that variant referenced repo-only paths (`scripts/scan.py`, `docs/*`) that do not
exist once copied elsewhere.

## Decision

The portable `skills/phase0-bootstrapper/` is the **single source of truth**.
`.claude/skills/phase0-bootstrapper/` is a **verbatim copy** of it — regenerated
(`rm -rf` + `cp -r`), never hand-edited. The two trees are byte-identical. The
canonical sensor stays `scripts/scan.py` (tests + CI); both trees run the bundled
localized copy at `resources/scan.py`.

## Why

The two trees must both exist: Claude Code discovers skills under
`.claude/skills/`, while the portable tree is what installs anywhere. The
question was how to keep them from drifting.

- **Symlink `.claude/` → portable** was the obvious de-dup, but Claude Code skill
  discovery does not document symlink-following (verdict: undocumented and
  version-dependent — too fragile to build on).
- **Drop `.claude/` entirely** breaks in-repo dogfooding — Claude Code would no
  longer find its own skill.
- **Keep two deliberately-different trees** is the status quo: permanent
  hand-sync toil and the exact divergence that produced the broken install.

A verbatim copy turns *semantic* divergence (two skills maintained in parallel)
into *mechanical* duplication (one source, one derived mirror) that a
deterministic test can lock with an exact diff (see #14). It also makes the
global install correct, because the copied tree is the self-contained one.

## Why this is an ADR

Hard to reverse — it sets the skill-packaging convention. Surprising without
context — a reader sees two byte-identical trees and assumes a drift bug rather
than a deliberate mirror, and will ask "why not a symlink?"; this records the
answer. A real trade-off — verbatim copy was chosen over symlink, drop-one, and
two-divergent-trees, each rejected for the reasons above. A companion ADR landing
with #14 covers the separate `docs/` ↔ `resources/` localization of the bundled
copies.
