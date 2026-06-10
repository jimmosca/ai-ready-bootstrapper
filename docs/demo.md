# Demo: bootstrap a fixture repo

A short walkthrough of the **infer → interview → write** flow against a bundled
sample repository. Everything is **read-only** on the target except the living
convention surface it writes (`AGENTS.md` / `CONTEXT.md` / `docs/adr/`) and the
internal `.ai/phase0/scan.json` — and only after you consent to the preview.

## 1. Setup

```bash
uv sync   # create the venv for the read-only scan sensor (zero runtime deps)
```

## 2. Pick a fixture

The repo ships realistic sample repositories under `tests/fixtures/` (they need
**no** dependency installation):

- `python_fastapi_repo` — FastAPI service with tests + CI
- `node_typescript_repo` — Node/TypeScript with npm scripts
- `terraform_repo` — Terraform/IaC
- `dbt_repo` — dbt project
- `mixed_data_ai_repo` — Python backend + mocked LLM provider + Terraform

Copy one somewhere writable so the demo writes its surface into a throwaway repo:

```bash
cp -r tests/fixtures/python_fastapi_repo /tmp/demo
```

## 3. Infer — run the read-only sensor

```bash
python scripts/scan.py /tmp/demo        # prints scan.json to stdout
```

The sensor walks the repo read-only and emits the inventory — languages, top-level
listing, manifests, detected commands, secret locations, glossary-term candidates, and the
**detected state** (virgin / partial / already-bootstrapped). It writes nothing
except (optionally) `/tmp/demo/.ai/phase0/scan.json` for audit.

## 4. Interview + write — drive the skill

Invoke the **phase0-bootstrapper skill** on `/tmp/demo`. It:

1. reads the scan, classifies the state, and (if not virgin) plans a **merge**,
   not a recreate;
2. **interviews** you — surfacing the open questions and low-confidence
   inferences (e.g. "Is `vitest` actually the canonical test command?", "What is
   the domain term behind the `billing/` module?");
3. shows a **dry-run preview** of every proposed write (which files, which managed
   blocks) and waits for your **explicit consent**;
4. on consent, writes the surface through managed markers.

Non-interactive run (no human available):

```text
phase0-bootstrapper --no-interview   # methodology + ADR-0001 always; repo
                                     # knowledge left as "Open questions"
```

## 5. Where the surface appears

A virgin `/tmp/demo` ends up with:

```
/tmp/demo/
  AGENTS.md                # routing entrypoint: what-this-is · canonical commands ·
                           #   how we work · Upkeep Contract · Start here · pointers
  CONTEXT.md               # (lazy) shared language — only if the interview confirmed terms
  docs/adr/
    0001-adopt-living-convention-methodology.md   # always (dogfood)
    NNNN-*.md              # (lazy) repo-specific confirmed decisions
  .ai/phase0/scan.json     # internal sensor output (audit / re-bootstrap)
```

Everything inside the managed blocks is generated; everything outside them is
yours. Start reading at `AGENTS.md`.

## 6. How to evaluate the output

There is no model judging the result — apply these checks:

1. **Write set respected.** `git status` in `/tmp/demo` shows changes confined to
   `AGENTS.md`, `CONTEXT.md`, `docs/adr/*`, and `.ai/phase0/*`
   (see [safety-policy.md](safety-policy.md)).
2. **Markers honored.** Every edit to a pre-existing file sits inside
   `<!-- phase0:start -->…<!-- phase0:end -->`; prose outside is untouched.
3. **Idempotent.** Run the skill twice — the second run produces **no diff**
   outside the managed blocks.
4. **Merge-safe.** Run it against a repo that already has an `AGENTS.md` (e.g.
   this repo) and confirm the human prose outside the markers is preserved.
5. **Skeleton complete.** The generated `AGENTS.md` has the six sections — and the
   Upkeep Contract, "How we work", and pointers to `CONTEXT.md` / `docs/adr/`;
   `docs/adr/0001-*` exists.
6. **No leaked secrets.** No secret value appears anywhere; secret-bearing files
   show up only by location.
7. **Epistemic honesty.** Confirmed claims cite `path:line`; the unconfirmed are
   explicit open questions (with "no automated verification found" as #1 when the
   scan finds no verification loop) — never guessed.

The FastAPI fixture has tests + CI + detectable commands, so its *Canonical
commands* section is exigible. Run against `terraform_repo` or `dbt_repo` to see
the **"no automated verification found"** open question lead the surface instead.
