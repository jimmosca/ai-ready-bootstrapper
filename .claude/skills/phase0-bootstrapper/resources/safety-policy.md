# Safety Policy

The operational rules that keep phase0-bootstrapper safe. It writes to a repo's
root files now, so the guarantee is no longer "read-only everywhere" but
**confined, marker-merged, consented writes** — and read-only everywhere else.
When in doubt, do less and log an `[OPEN]` question.

## The write set

The **only** paths the bootstrapper may create or modify:

- `AGENTS.md` (root)
- `CONTEXT.md` (root)
- `docs/adr/*` (new ADR files)
- `.ai/phase0/*` (the internal `scan.json`)

Everything else in the target repo is **read-only**. Source files are never
edited, renamed, or deleted.

## Managed-marker merge rule

- Writes into an **existing** file happen **only** inside the managed block
  `<!-- phase0:start -->…<!-- phase0:end -->`. Prose outside the markers is never
  edited, reordered, or removed.
- A fresh file (virgin repo) is created whole; an existing one is merged, not
  recreated.
- **`docs/adr/` and `CONTEXT.md` are additive:** ADR-0001 is written only if no
  methodology ADR already exists; terms are added, not replaced.
- **`CLAUDE.md` is not duplicated:** if it exists, respect it and ensure it routes
  to `AGENTS.md` (the canonical entrypoint).
- Re-running replaces only the managed block → **idempotent**: a second run
  changes nothing outside it.

## Dry-run and consent

- Consent gates **surface** writes: because root files are touched, every run
  **previews** the proposed writes to `AGENTS.md` / `CONTEXT.md` / `docs/adr/`
  (a dry-run diff: which files, which managed blocks) and waits for **explicit
  consent** before writing them. The sensor's internal `.ai/phase0/scan.json`
  (machine-readable audit output, no human prose, idempotent overwrite) is written
  without a prompt — it is the sensor running, not a surface edit.
- State detection gates this too: an **already-bootstrapped** repo is declined
  with a top-up offer rather than overwritten (see the SKILL.md contract).

## Still forbidden (unchanged from read-only days)

- Editing / creating / deleting any path **outside the write set** — especially
  source code.
- Running build / test / install / run / format / lint / codegen, or any project
  script or binary from the target repo.
- Any **git write**: `commit`, `add`, `checkout`, `switch`, `reset`, `stash`,
  `clean`, `rebase`, `merge`, `push`, `pull`, `tag`, `restore`.
- Mutating the **remote or infra**: creating labels, branches, or PRs; applying
  Terraform/k8s; running migrations. Day zero **documents and offers** consented
  snippets (e.g. `gh label create`), it does not execute them.
- Package-manager installs (`npm/pnpm/yarn/pip/uv/poetry/go/cargo/mvn/gradle …`).
- Network calls that download dependencies or mutate remote state.

## Dangerous commands (never run)

Illustrative, not exhaustive — the principle (no source mutation, no execution,
no remote/infra change) governs:

- `rm`, `mv`, `cp` over repo files, `>`/`>>` redirection into files outside the
  write set, `sed -i`, `truncate`, `chmod`, `chown`.
- `npm install`, `pip install`, `make`, `./gradlew`, `docker build/run`,
  `terraform apply`, `kubectl apply`, `prisma migrate`, `alembic upgrade`.
- `git commit/push/reset --hard/clean -fd/checkout .`.
- `curl`/`wget` that POST/PUT/DELETE or download into the tree.

## The scan script is LLM-free; the interview is agentic

The old "no LLM at all" rule is relaxed and **split**:

- **`resources/scan.py`** (the read-only sensor) stays **deterministic and
  LLM-free** — same input, same `scan.json`. No model calls, no network.
- **The interview and the write phase are agentic by nature** — an agent reasons
  over the scan, asks the maintainer, and drafts the surface. That is expected,
  not a violation. The agent still obeys the write set, markers, and consent
  rules above.

## Secrets handling

- If a real secret is found (`.env` with values, keys, tokens), record only its
  **existence and location** — as an open question or risk line in the surface,
  never the value. `.env.example` and schema files may be read to understand
  required config.
- Redact any incidental secret/PII from all written output.

## How to handle uncertainty

- Unsure whether an action mutates state, has side effects, or falls outside the
  write set → **don't do it**; record an `[OPEN]` question.
- A fact that cannot be verified read-only → downgrade to `[INFERENCE]` /
  `[ASSUMPTION]` with the reason, or take it to the interview; never assert it as
  `[FACT]`.
- Repo too large to inspect fully → sample breadth-first and record the sampling
  boundary as an `[ASSUMPTION]`.
- Prefer "unknown" over a confident guess.

## Self-check (run before finishing)

- `git status` confirms changes are confined to the write set (`AGENTS.md`,
  `CONTEXT.md`, `docs/adr/*`, `.ai/phase0/*`).
- Every edit to a pre-existing file is inside `<!-- phase0:start -->…<!-- phase0:end -->`.
- A re-run produces no diff outside the managed blocks (idempotent).
- No forbidden command ran; no remote/infra was mutated; no secret value appears
  in any written file.
