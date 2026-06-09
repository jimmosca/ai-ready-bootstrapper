# Phase 0 Contract

The formal contract of the **phase0-bootstrapper**. This is the source of truth;
the skill at `.claude/skills/phase0-bootstrapper/` (and its portable twin under
`skills/`) implements it. Terms used here are defined in
[`../CONTEXT.md`](../CONTEXT.md); the work loop they plug into lives in
[`../AGENTS.md`](../AGENTS.md).

## What phase0-bootstrapper does

- Enters an unknown / legacy repository and brings it to the **living convention
  surface** — `AGENTS.md` + `CONTEXT.md` + `docs/adr/` — via
  **infer → interview → write**.
- **Infer (read-only):** inspects structure, tooling, commands, and candidate
  glossary terms; builds an internal draft of facts (`path:line`), inferences
  (with confidence), and open questions. Writes nothing yet.
- **Interview:** surfaces the open questions and low-confidence inferences to a
  maintainer; answers promote inferences to facts and reveal decisions (→ ADR)
  and domain terms (→ `CONTEXT.md`).
- **Write (lazy, merged):** seeds only the artifacts that have real content, in
  their standard locations, through managed markers, then **stops**.
- Installs an **Upkeep Contract** so the surface stays current as the repo
  changes (see [`../CONTEXT.md`](../CONTEXT.md)).

It is a **day-zero installer for humans and agents alike** — not a documentation
generator, and not a maintainer.

## What phase0-bootstrapper does NOT do

- Does **not** edit, refactor, or fix any existing source file; the only writes
  are to the surface (see [safety-policy.md](safety-policy.md)).
- Does **not** run build / test / install / run / format / codegen commands, or
  any project script.
- Does **not** mutate the remote or infra (no git writes, no label/branch
  creation — it documents and offers consented snippets instead).
- Does **not** perform day-N upkeep. Maintenance is delegated to ecosystem skills
  (`grill-with-docs`, `to-prd`, `improve-codebase-architecture`).
- Does **not** materialize a bespoke artifact tree. Everything rises to the three
  standard files, leaves as an issue, or is dropped — no parallel taxonomy.

## Input contract

- **Required:** a path to a target repository (ideally a git repo; if not, the
  surface notes `vcs: none`).
- **Optional:** a focus hint (area or upcoming task) to bias breadth-first
  sampling. Absence of a hint = general-purpose bootstrap.
- **Optional `--no-interview`:** non-interactive mode for runs without a human
  (see *Degradation* below).
- **Assumed environment:** read access to the working tree; standard read-only
  tooling (`git`, `find`, `ls`, file read, text search). No network, credentials,
  or build environment is required or used.

## Output contract

- The deliverable is the **living convention surface**, merged into the repo's
  existing files — never a fresh bespoke tree. Exact artifacts, sections, and
  skeletons: [output-schema.md](output-schema.md).
  - **`AGENTS.md`** (root) — the routing entrypoint with the fixed six-section
    skeleton, including the **Upkeep Contract**.
  - **`CONTEXT.md`** (root, *lazy*) — shared language, only if the interview
    confirms terms.
  - **`docs/adr/NNNN-*.md`** (*lazy*) — only confirmed, hard-to-reverse decisions.
- **Lazy:** an artifact is written only when it has real content; nothing is
  fabricated to fill a slot.
- **Merged, not clobbered:** writes into an existing file touch only the managed
  block `<!-- phase0:start -->…<!-- phase0:end -->`; human prose is preserved.
  Re-running replaces only that block — **idempotent**.
- **Internal (minimal):** `<target-repo>/.ai/phase0/scan.json`, the sensor's
  output, kept for audit and re-bootstrap.
- Confirmed claims carry an inline `path:line` citation; everything unconfirmed
  is an explicit open question, never guessed (see
  [evidence-policy.md](evidence-policy.md)).

## State detection

The bootstrapper detects the target's state on start and acts accordingly:

- **Virgin** (no `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md`/`docs/adr/`) → install the
  full surface.
- **Partial** → merge into what exists; never recreate. If `CLAUDE.md` exists,
  respect it and ensure it routes to `AGENTS.md`.
- **Already bootstrapped** (healthy `CONTEXT.md` + ADRs + an Upkeep Contract) →
  not day zero: decline and offer a **top-up** (e.g. add the Upkeep Contract if
  missing).

## Degradation (`--no-interview`)

Day zero has two independent halves:

- **Methodology** (does not need to know the repo) → **always written**: the
  `AGENTS.md` skeleton, the "How we work" loop, the Upkeep Contract, and
  **ADR-0001** (the methodology decision). The bootstrapper dogfoods — writing
  ADR-0001 is its first act.
- **Repo knowledge** (needs confirmation) → **only with an interview**:
  `CONTEXT.md`, repo-specific ADRs, confirmed risks.

In `--no-interview`: run the scan, write `AGENTS.md` with what is factual (what
the repo is, Start-here, **only `[FACT]` commands**), the methodology, the
contract, and an **"Open questions for a maintainer"** section for what remains
unconfirmed; write ADR-0001; do **not** invent `CONTEXT.md` or repo ADRs. The
result is *provisional*, not false.

## Safety, evidence, and the loop

- **Safety:** writes are confined to the surface plus `.ai/phase0/`; merges touch
  only managed markers; a **dry-run preview + explicit consent** precedes any
  write. Full allow/deny list: [safety-policy.md](safety-policy.md).
- **Evidence:** the `[FACT]/[INFERENCE]/[ASSUMPTION]/[OPEN]` tags are the
  discipline of the infer→interview method, not a filing system. Confirmed →
  inline `path:line`; unconfirmed → open question. See
  [evidence-policy.md](evidence-policy.md).
- **The loop:** the surface this installs (the RPI+Verify loop, the Verify gate)
  is the methodology agents then work by — defined once in
  [`../AGENTS.md`](../AGENTS.md) and [ADR-0001](adr/0001-adopt-living-convention-methodology.md),
  not repeated here.

## Intended consumers

- **Human maintainers and coding agents alike** read the same surface: `AGENTS.md`
  first, then `CONTEXT.md` and `docs/adr/` as needed. The surface is optimized for
  both — humans validate and answer open questions; agents act safely from it.
- **Reviewers** trace a later plan back to the ADRs and the inline `path:line`
  citations.
