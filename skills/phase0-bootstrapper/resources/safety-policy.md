# Safety Policy

The operational rules that make Phase 0 read-only. When in doubt, do less and
log an `[OPEN]` question.

## What "read-only" means in practice

- The target repo's existing files are **never** created, edited, renamed, or
  deleted.
- The **only** permitted write is the new `<target-repo>/.ai/phase0/` directory
  and the 11 files inside it.
- No process is started that compiles, downloads, mutates state, or has side
  effects (no build/test/install/run/format/codegen, no servers, no migrations).
- No `git` command that writes history or working tree.
- No network action that mutates anything; no sending repo contents to external
  services beyond what the host agent already does to operate.

## Allowed operations

- Read files (`cat`/Read), list (`ls`, `find`), search (`grep`/ripgrep).
- `git status`, `git log`, `git ls-files`, `git show`, `git blame`,
  `git rev-parse HEAD`, `git diff` (read-only inspection).
- Read manifests, lockfiles, CI configs, Dockerfiles, `.env.example`/config
  *schemas*, and docs.
- Compute file stats (counts, sizes, language mix).
- Dispatch **read-only** sub-agents for breadth-first exploration that return
  summaries.
- Write only inside `.ai/phase0/`.

## Forbidden operations

- Editing/creating/deleting any path outside `.ai/phase0/`.
- Running build/test/install/run/format/lint/codegen or any project script.
- Any `git` write: `commit`, `add`, `checkout`, `switch`, `reset`, `stash`,
  `clean`, `rebase`, `merge`, `push`, `pull`, `tag`, `restore`.
- Package manager installs (`npm/pnpm/yarn/pip/uv/poetry/go/cargo/mvn/gradle …`).
- Executing scripts or binaries from the target repo.
- Reading or copying real secret **values** (see below).
- Network calls that download dependencies or mutate remote state.

## Dangerous commands (never run)

These are illustrative, not exhaustive — the principle (no mutation, no
execution) governs. Treat anything resembling these as forbidden:

- `rm`, `mv`, `cp` into the repo, `>`/`>>` redirection into repo files,
  `sed -i`, `truncate`, `chmod`, `chown`.
- `npm install`, `pip install`, `make`, `./gradlew`, `docker build/run`,
  `terraform apply`, `kubectl apply`, `prisma migrate`, `alembic upgrade`.
- `git commit/push/reset --hard/clean -fd/checkout .`.
- `curl`/`wget` that POST/PUT/DELETE or download into the tree.

## Secrets handling

- If a real secret is found (`.env` with values, keys, tokens), record only its
  **existence and location** as a risk in `risk-register.md`. Never read,
  reproduce, paste, or transmit the value.
- `.env.example` and schema files may be read to understand required config.
- Redact any incidental secret/PII from all output (esp. `agent-handoff.md`).

## How to handle uncertainty

- If unsure whether an action mutates state or has side effects → **do not do
  it**; record an `[OPEN]` question instead.
- If a fact cannot be verified read-only → downgrade it to `[INFERENCE]` or
  `[ASSUMPTION]` with the reason, never assert it as `[FACT]`.
- If the repo is too large to inspect fully → sample breadth-first and record the
  sampling boundary in `manifest.yaml.coverage` and as an `[ASSUMPTION]`.
- Prefer "unknown" over a confident guess.

## Self-check (run before finishing)

- `git status` confirms changes are confined to `.ai/phase0/`.
- No forbidden command was executed.
- No secret value appears anywhere in the output.
