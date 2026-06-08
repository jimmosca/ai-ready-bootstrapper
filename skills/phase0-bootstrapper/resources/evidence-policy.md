# Evidence Policy

How Phase 0 separates what it *knows* from what it *guesses*. This is the
discipline that makes the pack trustworthy. Evidence over vibes.

## The four epistemic tags

Every non-trivial claim carries exactly one tag:

- **`[FACT]`** — directly observed in the repo. **Must** cite evidence: a
  `path:line` reference or a read-only command + its output. Gets an evidence ID
  (`E#`) recorded in `evidence-map.md`.
  *e.g.* `[FACT] Test runner is vitest. evidence: E12 (package.json:31)`
- **`[INFERENCE]`** — a conclusion reasoned from one or more facts. **Must** cite
  the supporting evidence IDs and a `confidence` level.
  *e.g.* `[INFERENCE] HTTP layer is Express. confidence: high. from E4, E7`
- **`[ASSUMPTION]`** — taken as true to make progress, but unverified. **Must**
  state what would confirm or refute it, and the impact if wrong.
  *e.g.* `[ASSUMPTION] Postgres is the prod DB (only docker-compose seen). Confirm via infra/. Impact: high.`
- **`[OPEN]`** — an unresolved question for a human or later agent.
  *e.g.* `[OPEN] Which service owns auth token rotation?`

A claim with no tag is not allowed. A `[FACT]` with no evidence is not a fact —
downgrade it to `[INFERENCE]` or `[ASSUMPTION]`.

## Confidence levels (for inferences)

- **high** — multiple independent signals agree (e.g. manifest + import + CI all
  point the same way).
- **medium** — one solid, direct signal.
- **low** — weak, indirect, or convention-based signal (a guess from naming or
  defaults). Low-confidence inferences should usually also raise an `[OPEN]`.

## Evidence format

- Inline: `evidence: E#`. Resolve every `E#` in `evidence-map.md` as:
  `E# | <short claim> | <path:line | command> | <file|command|config>`.
- `path:line` for a specific location (clickable); `path` alone only when the
  whole file is the evidence.
- Command evidence: record the **read-only** command and the relevant output
  excerpt, not a paraphrase.
- One evidence ID per distinct source; reuse the same `E#` when multiple claims
  rest on the same source.

## Counter-evidence format

When signals conflict, record both — do not silently pick a winner:

- Note it on the claim: `[INFERENCE] … confidence: low. supports: E4; contradicts: E9`.
- Prefer the more authoritative source (CI/lockfile/source code) over the less
  authoritative (README/comments/naming), and say why.
- If the conflict is material and unresolved, raise an `[OPEN]` question and
  lower confidence accordingly.

## Rules for avoiding hallucinated architecture claims

1. **No component, dependency, datastore, or data flow may be asserted as
   `[FACT]` without a `path:line`.** If you cannot point to it, it is at best an
   `[INFERENCE]` with stated confidence.
2. **Names are not behavior.** A file called `cache.ts` is evidence of a name,
   not proof of caching — tag accordingly.
3. **Do not invent versions, flags, endpoints, or config keys.** Quote them from
   source or omit them.
4. **Absence ≠ non-existence.** "No tests found in inspected paths" is an
   `[OPEN]`/`[ASSUMPTION]` bounded by what you sampled, not a `[FACT]` that none
   exist.
5. **Diagrams require evidence.** Only draw an edge/box you can trace to a
   `path:line`.
6. **Prefer "unknown".** An honest gap is more useful to the next agent than a
   confident fabrication.
