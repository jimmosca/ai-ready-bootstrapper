# Agent Handoff

## What this repo is
python_fastapi_repo — Python; languages: Python.

## Start here
1. `manifest.yaml` for the machine-readable index + readiness.
2. `repo-map.md` and `commands-and-tooling.md`.
3. `risk-register.md` and `assumptions-and-open-questions.md` before editing.

## Commands (detected, NOT executed)
Nothing was run — this is a read-only pack.

**Found in manifests (`[FACT]`):**
_none_

**Inferred (`[INFERENCE]`, verify before trusting):**
- `pytest`  (inferred, medium)
- `ruff check`  (inferred, medium)
- `ruff format`  (inferred, medium)
- `mypy .`  (inferred, medium)

## Top risks
- none recorded

## Safe-change rules
- See `safe-change-boundaries.md`. Avoid manifests/lockfiles/infra without a plan.

## Biggest unknowns
- What is the project's purpose and who owns it?
- How are changes validated before merge (tests/CI)?
- What is the primary runtime entrypoint and deployment target?

## Suggested next step (Research → Plan → Implement)
Resolve the open questions (esp. how changes are verified) before planning any
implementation. Do not start Implement until a verification loop is confirmed.
