# Output Schema

The artifacts of the **living convention surface** and their shape. For each:
**Purpose**, **Required sections**, **Must not include**, **Skeleton**. Skeletons
are the canonical minimum; a worked example lives in
`resources/examples/standard-output/` (this directory).

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
     The bullets carry the full discipline: **Research** delegates a wide
     read-only sweep to a subagent that returns a synthesis (protect the main
     window); **Plan** writes the plan to disk and grills it for any non-trivial
     change; **compact intentionally** — durable research/plan artifacts on disk,
     working window lean, reset to fresh context rather than letting it bloat. The
     **Verify** bullet carries the run discipline: run the suite when something it
     *executes* changed (not docs/comments) and once as the pre-push gate; never
     re-run a green deterministic suite just to recover its output.
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
## How we work here          (RPI → Verify, ~5 bullets; subagent sweep · plan-to-disk · intentional compaction; skills)
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
  is a valid ADR.
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

Not part of the surface — the read-only **sensor**'s (`resources/scan.py`)
machine-readable output, persisted for audit and re-bootstrap. It is the only
thing written outside `AGENTS.md` / `CONTEXT.md` / `docs/adr/`, and the only write
exempt from the consent gate (see [safety-policy.md](safety-policy.md)). It is a
**versioned interface** the skill consumes: this field list plus the sensor's
tests are its contract (no separate JSON-Schema file).

Top-level fields:

- `schema_version`, `generator` — interface version and producer.
- `repo` — `{name, root, vcs, head_commit, file_count, languages}`.
- `project_types` — likely ecosystem(s); includes `"mixed repo"` when more than one.
- `important_files` — category → relative paths (readme, manifests, tests, CI, …).
- `commands` — detected build/test/lint/run commands, each
  `{category, command, source, finding_type, confidence}`. Found verbatim in a
  manifest → `fact`; inferred from tooling → `inference` with a confidence level
  (never executed).
- `top_level`, `excluded_dirs`, `secret_files` — the inspected top-level listing,
  the ignored dirs pruned from the walk, and secret-bearing files (location only,
  never read).
- `glossary_candidates` — proposed domain-term candidates (names, not meanings),
  each `{term, kind, occurrences, sources}` with `kind` ∈
  `directory | identifier | readme`. Candidates only — the interview confirms them.
- `state` — `{status, signals}`. `signals` are presence booleans
  (`agents_md, claude_md, copilot_instructions, context_md, adr_dir, context_map,
  upkeep_contract`);
  `status` (`virgin | partial | already-bootstrapped`) is a **presence-based hint**,
  not a health verdict — the skill makes the final decline/top-up call.
