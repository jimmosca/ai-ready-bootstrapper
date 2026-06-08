---
name: phase0-bootstrapper
description: >-
  Use when entering an unknown, legacy, or unfamiliar repository (software,
  data, or AI/ML) that lacks agent-ready context. Inspects the repo READ-ONLY
  and writes a lean, evidence-backed Phase 0 context pack to
  <target-repo>/.ai/phase0/ (repo map, architecture, entrypoints, commands +
  verification surface, risks, safe-change boundaries, decision log, evidence
  map, agent handoff). Trigger on "bootstrap this repo", "make this repo
  AI-ready", "generate a Phase 0 / context pack", or before starting work in an
  unfamiliar codebase.
---

# Phase 0 Bootstrapper

Compiles the **Research artifact** a future coding agent starts from: enter an
unknown repo, inspect it without changing it, and write a lean, evidence-backed
context pack to `<target-repo>/.ai/phase0/`. It is a context compiler for
agents, not documentation for humans.

## When to use

- Starting work in a repo you (or the next agent) don't already understand.
- A legacy/handed-over codebase with no agent-ready context.
- The user asks to "bootstrap", "make AI-ready", or "generate a Phase 0 pack".
- Before planning a change in an unfamiliar area, to establish ground truth.

## When NOT to use

- The repo is already well-understood or an up-to-date `.ai/phase0/` exists
  (re-run only with explicit consent; overwriting needs `--force`).
- The task is to **change** code — that is Plan/Implement, not Phase 0.
- You only need one fact (just read that file); Phase 0 produces the full pack.
- The path is not a repository, or is a system/home root (refuse — see limits).

## Allowed actions (read-only)

- Read files; list directories; search/grep.
- `git status`, `git log`, `git ls-files`, `git show`, `git blame`,
  `git rev-parse HEAD`, `git diff` — read-only inspection only.
- Read manifests, lockfiles, CI configs, Dockerfiles, `.env.example`/config
  *schemas*, and docs. Compute file stats (counts, sizes, language mix).
- Write **only** inside `<target-repo>/.ai/phase0/`.

## Forbidden actions

- Editing, creating, renaming, or deleting any path outside `.ai/phase0/`.
- Running build/test/install/run/format/lint/codegen or any project script.
- Any `git` write (commit, add, checkout, reset, stash, clean, rebase, merge,
  push, pull, tag, restore).
- Package installs (`npm/pnpm/yarn/pip/uv/poetry/go/cargo/mvn/gradle …`).
- Executing scripts or binaries from the target repo.
- Reading or copying real secret **values**; network calls that download deps
  or mutate remote state.
- If unsure whether an action mutates state → do not do it; log an `[OPEN]`.

## Explicit safety limits

- **Only write path:** `<target-repo>/.ai/phase0/` (created on a real run).
- **Per-file read cap:** ≤ 1 MB; do not load larger files into context.
- **Excluded from the walk:** `.git`, `.venv`, `venv`, `node_modules`,
  `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `dist`, `build`,
  `target`, `__pycache__`, and similar caches/build output.
- **Commands are detected, never executed.** An unrun command is `[INFERENCE]`,
  never `[FACT]`.
- **Secrets:** record only existence + location of any real secret; never read,
  paste, or transmit the value. `.env.example`/schemas may be read.
- **Refuse** to scan a non-existent path or a system/home root (`/`, `/home`,
  `/etc`, `/usr`, …).

## Workflow

Prefer the CLI when it is installed; otherwise do the same steps manually.

**With the `phase0` CLI (preferred):**
1. **Confirm scope.** Get the target repo path. If missing, ask for it. Confirm
   the default output `<repo>/.ai/phase0/` (or an `--output-dir`).
2. **Dry-run first.** `phase0 scan --repo-path R --dry-run` — prints the summary
   (project types, findings, risks, open questions) and writes nothing.
3. **Generate.** `phase0 scan --repo-path R` writes the 11-file pack to
   `R/.ai/phase0/`. Use `--force` only to overwrite an existing non-empty pack.
4. **Evaluate.** Open the pack: every `[FACT]` cites an `E#` that resolves in
   `evidence-map.md`; `manifest.yaml` says `mode: read-only`; uncertainty is
   tagged, not hidden. The CLI validates evidence references on generation.
5. **Report.** Give the user a concise summary (below) and point them at
   `agent-handoff.md`.

**Manual (no CLI), same outcome — work the phases in order, writing each file as
you finish it so you don't hold everything in context:**
1. **Confirm & orient.** Confirm the path; note whether it's a git repo; take a
   top-level snapshot (root listing, file count, language mix). Create
   `.ai/phase0/` — the only directory you create.
2. **Inspect read-only.** Walk the tree (skip the excluded dirs above), reading
   manifests/configs/CI/docs within the read cap. Detect: **project type**,
   **tooling** (build/test/lint/format/typecheck/deploy), **entrypoints**,
   **tests**, **CI**, **docs**, and **architecture hints** (components, data
   flow, datastores, external services).
3. **Write the pack.** Produce the 11 files per `resources/output-schema.md`,
   tagging every claim `[FACT]`/`[INFERENCE]`/`[ASSUMPTION]`/`[OPEN]` per
   `resources/evidence-policy.md`. Mark detected commands "detected, not
   executed". Record risks (missing tests/CI, secrets present, unpinned deps)
   with severity + likelihood + evidence. Do not invent ADRs, versions, or
   endpoints.
4. **Evaluate.** Self-check: `git status` shows changes confined to
   `.ai/phase0/`; every `[FACT]` has evidence; no secret value appears; every
   file is non-empty; the manifest coverage lists what could NOT be determined.
5. **Report.** Concise summary; point at `agent-handoff.md`.

**Never modify source code during Phase 0.** The only write is `.ai/phase0/`.

## Expected outputs

`<target-repo>/.ai/phase0/` (11 files):

```
manifest.yaml          repo-map.md          architecture.md
entrypoints.md         commands-and-tooling.md
decision-log.md        assumptions-and-open-questions.md
risk-register.md       safe-change-boundaries.md
agent-handoff.md       evidence-map.md
```

See `resources/examples/minimal-output/` for a real, unedited pack, and
`resources/output-schema.md` for each file's required sections.

## Quality bar

- Every `[FACT]` cites an `E#` resolving in `evidence-map.md`; no fact without
  evidence (downgrade to `[INFERENCE]`/`[ASSUMPTION]`).
- Inferences carry a confidence level; low-confidence ones also raise an
  `[OPEN]`. "Unknown" is preferred over a confident guess.
- Detected commands are tagged `[INFERENCE]` unless found verbatim in a manifest
  (`[FACT]`); none were executed.
- No invented components, versions, flags, endpoints, or ADRs. Names are not
  behavior.
- Lean and gotcha-first: capture the non-obvious; omit what the code makes
  obvious. Every file non-empty and internally consistent.
- The pack writes nothing outside `.ai/phase0/`.

## Handoff behavior

Finish by directing the next agent to `agent-handoff.md` (the lean entrypoint:
what the repo is, where to start, **verified** commands only, readiness
scorecard, top risks, biggest unknowns, suggested RPI next step) and
`manifest.yaml` (machine-readable index). Everything else is linked from there;
do not duplicate it into chat.

Concise user summary to print (CLI prints this for you):

- repo path · detected project type(s)
- output path (or "nothing written" for a dry run)
- counts: findings · risks · open questions
- suggested next step (Research → Plan before Implement)

## Trigger examples

- "Bootstrap this repo / generate a Phase 0 context pack."
- "Make this codebase AI-ready."
- "I just cloned this legacy service and don't understand it — map it out."
- "Before we change the billing module, give me the lay of the land."
- "Create the `.ai/phase0/` pack for this project."

## References (bundled, self-contained)

- `resources/output-schema.md` — the 11 files: purpose, required sections, what
  to exclude, skeletons.
- `resources/safety-policy.md` — allowed vs. forbidden operations, dangerous
  commands, secrets handling, uncertainty rules.
- `resources/evidence-policy.md` — the four epistemic tags, confidence levels,
  evidence format, anti-hallucination rules.
- `resources/examples/minimal-output/` — a real generated pack.
