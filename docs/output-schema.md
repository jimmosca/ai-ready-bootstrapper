# Output Schema

The artifacts of the **living convention surface** and their shape. For each:
**Purpose**, **Required sections**, **Must not include**, **Skeleton**. Skeletons
are the canonical minimum; working copies live in
`.claude/skills/phase0-bootstrapper/templates/` (and the portable
`skills/.../resources/`). This repo's own `AGENTS.md` / `CONTEXT.md` /
`docs/adr/` are the worked dogfood example.

Conventions (see [evidence-policy.md](evidence-policy.md)): confirmed claims
carry an inline `path:line`; the unconfirmed becomes an explicit open question.
Keep every artifact lean and pointer-first — **point, don't transcribe**.

## Managed-marker merge

Every write into an existing file is confined to a managed block:

```markdown
<!-- phase0:start -->
…generated content…
<!-- phase0:end -->
```

Human prose outside the markers is never touched; re-running replaces only the
block (idempotent). See [safety-policy.md](safety-policy.md).

---

## AGENTS.md (root) — the routing entrypoint

- **Purpose:** the one file an agent or human reads first. Routes to the rest;
  does not transcribe it. Highest-ROI artifact, so it gets a **fixed skeleton**.
- **Required sections (fixed order, by ROI):**
  1. **What this repo is** — 2–3 lines.
  2. **Canonical commands** — copy-pasteable build / test / lint / run / verify;
     the center of gravity. If the scan finds a verification loop, these are
     exigible; if it finds **none**, say so explicitly ("no automated
     verification found; high-risk changes; verify manually by X; **setting up
     verification is the first recommended task**") — that is open question #1.
  3. **How we work here** — the RPI+Verify loop in ~5 bullets, weight on the
     extremes; names the skills used (`grill-me` / `tdd` / `grill-with-docs`).
  4. **Start here** — pointers into the repo (where to begin reading), not copies.
  5. **Upkeep Contract** — the trigger-driven clause that keeps the surface
     current (ADR / new term / changed verification or "Start here" pointer →
     update in the same change; else write nothing).
  6. **Pointers** — `CONTEXT.md` and `docs/adr/`.
- **Must not include:** transcribed architecture, a risk dump, a changelog,
  duplicated code, or marketing prose. **Adopt, don't invent:** do not fabricate
  code-style / PR / security conventions the repo lacks → raise them as open
  questions or later upkeep. Soft budget **~120–150 lines**; overflow becomes
  pointers.
- **Skeleton:**
```markdown
# AGENTS.md
<!-- phase0:start -->
## What this repo is
## Canonical commands        (build / test / lint / run / verify — or "none found")
## How we work here          (RPI → Verify loop, ~5 bullets; skills referenced)
## Start here                (pointers, not copies)
## Upkeep Contract           (ADR / term / verification triggers → same change)
## Pointers                  (CONTEXT.md · docs/adr/)
<!-- phase0:end -->
```

## CONTEXT.md (root, lazy) — shared language

- **Purpose:** the glossary — the words this repo uses and what they mean, so
  humans and agents talk about the same thing. **Definitions, not mechanics.**
  Written only if the interview confirms real domain terms (lazy: no terms → no
  file). Components that used to live in an "architecture map" appear here as
  named terms, not as a transcribed diagram.
- **Required sections:** a short preamble (glossary-only; how-we-work lives in
  `AGENTS.md`, decisions in `docs/adr/`; update terms in the same change) and a
  **Terms** list. Each term: a heading, a one-paragraph definition, and an
  `_Avoid:_` line naming wrong synonyms.
- **Must not include:** mechanics or process (that is `AGENTS.md`), decisions and
  their rationale (that is `docs/adr/`), or unconfirmed candidate terms (those
  stay open questions). Names are not behavior — a term is a confirmed meaning,
  not a directory name.
- **Skeleton:**
```markdown
# CONTEXT.md
Shared language for this repo — definitions, not mechanics. How we work lives in
AGENTS.md; decisions live in docs/adr/. Update a term in the same change.
## Terms
### <Term>
<one-paragraph definition>
_Avoid:_ <wrong synonyms>
```

## docs/adr/NNNN-kebab-title.md (lazy) — durable decisions

- **Purpose:** record a decision that is **hard to reverse, surprising, or
  carries a real trade-off** (the three ADR triggers). Only confirmed decisions
  surfaced by the interview; nothing speculative. Naming follows the `docs/adr/`
  convention. ADR-0001 (the methodology) is always written (dogfood); repo ADRs
  are lazy.
- **Required sections:** Status + Date; Context; Decision; **Why this is an ADR**
  (which of the three triggers it meets); Consequences. A *rejected alternative*
  is a valid ADR (see [ADR-0002](adr/0002-no-enforcing-bdd.md)).
- **Must not include:** mechanics that belong in `AGENTS.md`, term definitions
  that belong in `CONTEXT.md`, or a decision re-stated as fact without its why.
  Point to the live surface instead of copying it.
- **Skeleton:**
```markdown
# NNNN — <decision, imperative>
- **Status:** Accepted
- **Date:** YYYY-MM-DD
## Context
## Decision
## Why this is an ADR     (hard to reverse / surprising / real trade-off)
## Consequences
```

---

## Internal: .ai/phase0/scan.json

Not part of the surface — the read-only sensor's machine-readable output,
persisted for audit and re-bootstrap. It carries the inventory (languages, tree,
manifests, detected commands, secret locations, glossary-term candidates, state
detection). It is the only thing written outside `AGENTS.md` / `CONTEXT.md` /
`docs/adr/`. See [safety-policy.md](safety-policy.md).
