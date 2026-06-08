# Demo: run Phase 0 against a fixture repo

A 2-minute walkthrough using a bundled sample repository. Everything here is
**read-only** on the target except the generated `.ai/phase0/` folder.

## 1. Setup

```bash
uv sync   # create the venv, install the package (zero runtime deps)
```

## 2. Pick a fixture

The repo ships realistic sample repositories under `tests/fixtures/` for
static analysis (they need **no** dependency installation):

- `python_fastapi_repo` — FastAPI service with tests + CI
- `node_typescript_repo` — Node/TypeScript with npm scripts
- `terraform_repo` — Terraform/IaC
- `dbt_repo` — dbt project
- `mixed_data_ai_repo` — Python backend + mocked LLM provider + Terraform

Copy one somewhere writable so the demo writes its pack outside the source tree:

```bash
cp -r tests/fixtures/python_fastapi_repo /tmp/demo
```

## 3. Example command

Preview first (writes nothing), then generate:

```bash
uv run phase0 scan --repo-path /tmp/demo --dry-run   # inspect only
uv run phase0 scan --repo-path /tmp/demo             # writes /tmp/demo/.ai/phase0/
```

Useful flags: `--output-dir DIR`, `--force` (overwrite a non-empty pack),
`--format json` (machine-readable summary).

## 4. Example output summary

```
phase0 scan summary
  repo path:       /tmp/demo
  project types:   Python
  output path:     /tmp/demo/.ai/phase0
  findings:        2
  risks:           0
  open questions:  3
  next step:       Research → Plan: resolve the open questions (esp. how changes are verified) before implementing.

Start at agent-handoff.md. See docs/phase0-contract.md.
```

(The FastAPI fixture has tests + CI + detectable commands, so the risk register
is empty. Run against `terraform_repo` or `dbt_repo` to see testing/verification
risks appear.)

## 5. Where the generated files appear

Under `<repo>/.ai/phase0/` — the **only** thing written:

```
/tmp/demo/.ai/phase0/
  manifest.yaml                      # machine-readable index + readiness scorecard
  repo-map.md                        # languages, layout, important files
  architecture.md                    # inferred components (low confidence)
  entrypoints.md                     # detected commands as entrypoints (not run)
  commands-and-tooling.md            # package manager, tooling, detected commands
  decision-log.md                    # evidence-backed decisions only
  assumptions-and-open-questions.md  # weak-signal assumptions + open questions
  risk-register.md                   # ranked, evidence-backed gaps
  safe-change-boundaries.md          # safe / caution / do-not-touch areas
  agent-handoff.md                   # lean entrypoint for the next agent
  evidence-map.md                    # E# -> path:line / command traceability
```

Start reading at `agent-handoff.md`; everything else links from there and from
`manifest.yaml`.

## 6. How to evaluate the output

Phase 0's evaluation is **deterministic** — no model judges the result. Apply
these checks (the first runs automatically on every generation):

1. **Evidence integrity (automatic).** Generation calls
   `Phase0Report.validate()`, which fails if any cited `E#` does not resolve in
   `evidence-map.md`. If `phase0 scan` succeeded, evidence references are sound.
2. **Read-only proof.** `git status` in the target shows changes confined to
   `.ai/phase0/`; `manifest.yaml` says `mode: read-only`.
3. **No leaked secrets.** No secret value appears in any file; secret-bearing
   files show up only by location in `risk-register.md`.
4. **Completeness.** All 11 files exist and are non-empty; `manifest.yaml`
   `coverage` lists what could not be determined.
5. **Epistemic honesty.** Every `[FACT]` cites an `E#`; inferences carry a
   confidence; unknowns are `[OPEN]`, not guessed.

You can reproduce check #1 and the structural checks directly:

```bash
uv run python - <<'PY'
from pathlib import Path
from phase0_bootstrapper.models import ScanTarget
from phase0_bootstrapper.renderer import build_pack, ALL_FILES

pack = build_pack(ScanTarget(repo_path=Path("/tmp/demo"),
                             output_dir=Path("/tmp/demo/.ai/phase0")))
pack.report.validate()                       # raises on any dangling E#
assert set(pack.files) == set(ALL_FILES)     # 11 files
assert all(c.strip() for c in pack.files.values())
assert "mode: read-only" in pack.files["manifest.yaml"]
assert all(f.evidence for f in pack.report.findings if f.type.value == "fact")
print("OK — evidence resolves, 11 files non-empty, read-only, facts cite evidence")
PY
```

Expected:

```
OK — evidence resolves, 11 files non-empty, read-only, facts cite evidence
```
