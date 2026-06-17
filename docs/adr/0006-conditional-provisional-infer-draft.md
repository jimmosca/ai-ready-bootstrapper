# 0006 — Conditional, provisional infer draft via a read-only subagent

- **Status:** Accepted
- **Date:** 2026-06-17

## Context

The bootstrapper's Infer phase reads broadly to build a draft (facts with
`path:line`, inferences with confidence, open questions) that the Interview then
sharpens. On a large or mixed repo, doing that sweep in the main window spends the
context budget on file contents that never need to stay resident — exactly the
waste the living-convention methodology ([ADR-0001](0001-adopt-living-convention-methodology.md))
tells agents to avoid (delegate wide read-only sweeps; compact intentionally).

Two facts shape the options. First, the breadth signal is already in hand:
`scan.json` carries `repo.file_count`, `project_types` (`"mixed repo"` when more
than one ecosystem), and `repo.languages` before Infer runs. Second, the write-set
glob is already `.ai/phase0/*` ([safety-policy.md](../safety-policy.md)), so
persisting a second internal file there widens no path. The tension is elsewhere:
the contract says "no parallel taxonomy" — everything rises to the three standard
files, leaves as an issue, or is dropped — and the only blessed internal artifact
so far is `scan.json`, which is **deterministic sensor output**. A persisted draft
is the opposite: a **non-deterministic LLM interpretation**.

## Decision

Make the Infer sweep **size-conditional**, governed by the `scan.json` breadth
signal (soft guide, ~150–200 files, OR'd with `"mixed repo"` / multiple languages):

- **Large / mixed** → run the sweep in a **read-only subagent** that returns *only*
  the structured draft, and **persist** that draft to `<target>/.ai/phase0/draft.md`
  at the Infer→Interview boundary.
- **Small** → infer **inline**; the draft stays in-context; nothing is written.

`draft.md` is written without a separate consent prompt (like `scan.json`), headed
**PROVISIONAL** with the generated timestamp and the source `repo.head_commit`.
Staleness is **deterministic**: on re-bootstrap, a current `head_commit` that
differs from the recorded one (or `vcs: none`) marks the draft stale → re-infer,
never trust it blind.

## Why this is an ADR

It is hard to reverse and surprising without context: it blesses a second internal
artifact that is an LLM interpretation, not sensor output — a change to the
execution model (a subagent now produces a persisted draft) and to the
anti-hallucination posture (a written artifact that must never be trusted as ground
truth). A future reader meeting `draft.md` would reasonably ask how it squares with
"no parallel taxonomy", given the earlier multi-file `.ai/phase0/` pack was retired
down to a single `scan.json`. The answer is the real trade-off recorded here: this
is **not** a parallel deliverable taxonomy — it is one internal, **conditional**,
**provisional** companion to `scan.json`, symmetric with it as audit/resume state,
with deterministic staleness so it cannot silently rot into a false ground truth.

## Consequences

- Large/mixed bootstraps keep the main window lean; the interview and any
  re-bootstrap resume from `draft.md` rather than conversational memory.
- Small repos are unaffected — no subagent spin-up, no file materialized.
- The sensor stays untouched and deterministic; the heuristic reuses fields it
  already emits. No new runtime dependency.
- A new failure mode to guard in review: a stale `draft.md` trusted blind. The
  recorded `head_commit` staleness check is the mitigation, and it is deterministic.
- The contract and safety policy now name `draft.md` as the one bounded exception
  to "no parallel taxonomy".
