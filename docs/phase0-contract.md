# Phase 0 Contract

The formal contract of the Phase 0 Bootstrapper. This is the source of truth;
the skill at `.claude/skills/phase0-bootstrapper/` implements it.

## What Phase 0 does

- Enters an unknown / legacy repository **read-only** and compiles a
  **context pack** at `<target-repo>/.ai/phase0/`.
- Inspects structure, tooling, entrypoints, and architecture; captures
  evidence; flags risks; marks safe-change boundaries; records open questions.
- Produces the **Research artifact** that future coding agents start from
  (the "R" in Research → Plan → Implement).

## What Phase 0 does NOT do

- Does **not** modify any existing file in the target repo.
- Does **not** run build / test / install / run / format / codegen commands.
- Does **not** write code, fix bugs, refactor, or open PRs.
- Does **not** plan or implement changes (that is a later phase).
- Does **not** produce human-marketing prose or exhaustive documentation. It is
  a context compiler for agents, kept lean and gotcha-first.

## Input contract

- **Required:** a path to a target repository (ideally a git repo; if not, the
  pack notes `vcs: none`).
- **Optional:** a focus hint (area or upcoming task) to bias breadth-first
  sampling. Absence of a hint = general-purpose bootstrap.
- **Assumed environment:** read access to the working tree; standard read-only
  tooling (`git`, `find`, `ls`, file read, text search).
- No network access, credentials, or build environment is required or used.

## Output contract

- A single new directory `<target-repo>/.ai/phase0/` containing exactly the 11
  files defined in [output-schema.md](output-schema.md).
- `manifest.yaml` is machine-readable and parseable **without** the prose files.
- Every factual claim is tagged and cites evidence per
  [evidence-policy.md](evidence-policy.md); all evidence IDs resolve in
  `evidence-map.md`.
- Unknowns are stated explicitly, never guessed. Confidence is reported.
- The pack is internally consistent: claims, tags, and evidence agree across
  files.

## Read-only guarantee

- The **only** filesystem write is creating `.ai/phase0/` and its files.
- After a run, `git status` shows changes limited to `.ai/phase0/` (plus, if the
  repo ignores it, an untracked `.ai/` directory). Nothing else is touched.
- See [safety-policy.md](safety-policy.md) for the operational allow/deny list.

## Intended consumers

- **Coding agents** (primary): read `agent-handoff.md` first, then drill into
  `manifest.yaml` and the specific files for a task. The pack is optimized for
  machine consumption and safe action.
- **Human maintainers:** validate inferences, answer open questions, and confirm
  safe-change boundaries.
- **Reviewers:** use `evidence-map.md` and `decision-log.md` to audit how a later
  agent's plan traces back to ground truth.

## Versioning

- `manifest.yaml.schema_version` tracks the output contract version. Breaking
  changes to the file set or required sections bump it.
