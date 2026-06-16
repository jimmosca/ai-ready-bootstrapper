# Evidence Policy

How phase0-bootstrapper separates what it *knows* from what it *guesses*. This is
**process discipline for the infer→interview method**, not a filing system: the
tags live in how the agent reasons, and the surface it writes carries inline
citations and explicit open questions — no separate evidence ledger. Evidence
over vibes.

## The four epistemic tags (in the method)

During **infer → interview**, every non-trivial claim carries exactly one tag:

- **`[FACT]`** — directly observed in the repo. Cite an inline `path:line` (or a
  read-only command + its output excerpt).
  *e.g.* `[FACT] Test runner is vitest (package.json:31).`
- **`[INFERENCE]`** — reasoned from one or more facts. State a `confidence` level.
  *e.g.* `[INFERENCE] HTTP layer is Express. confidence: high (imports + scripts).`
- **`[ASSUMPTION]`** — taken as true to make progress, unverified. State what
  would confirm or refute it, and the impact if wrong.
  *e.g.* `[ASSUMPTION] Postgres is the prod DB (only docker-compose seen). Confirm via infra/. Impact: high.`
- **`[OPEN]`** — an unresolved question for the interview or a later agent.
  *e.g.* `[OPEN] Which service owns auth token rotation?`

A claim with no tag is not allowed. A `[FACT]` with no `path:line` is not a fact —
downgrade it, or take it to the interview.

## The interview promotes evidence

The point of the interview is to **move claims up the ladder**: a maintainer's
answer turns an `[INFERENCE]`/`[ASSUMPTION]` into a `[FACT]` (now citable), or
resolves an `[OPEN]` into a decision (→ ADR) or a term (→ `CONTEXT.md`). What the
interview cannot confirm stays an explicit open question — it is never quietly
promoted.

## What lands in the written surface

The tags are scaffolding; they mostly **do not appear** in the final artifacts.
Instead:

- **Confirmed** → stated plainly with an inline `path:line` where the citation
  helps a reader verify (e.g. a canonical command, a key entrypoint).
- **Unconfirmed** → an explicit **open question**, surfaced where it matters
  (e.g. `AGENTS.md` "Open questions for a maintainer", or a risk line). The #1
  open question when no verification loop exists is called out by name (see
  [output-schema.md](output-schema.md)).
- **No `evidence-map.md`, no `E#` IDs, no `manifest.yaml`.** Traceability is the
  inline `path:line` itself; the only persisted machine artifact is the sensor's
  `.ai/phase0/scan.json` (audit, not citation ledger).

## Confidence levels (for inferences)

- **high** — multiple independent signals agree (manifest + import + CI).
- **medium** — one solid, direct signal.
- **low** — weak, indirect, or convention-based (a guess from naming or defaults).
  Low-confidence inferences should usually become an interview question or an
  `[OPEN]`.

## Citation format

- Inline `path:line` for a specific location (clickable); `path` alone only when
  the whole file is the evidence.
- Command evidence: the **read-only** command and the relevant output excerpt,
  not a paraphrase.

## Counter-evidence

When signals conflict, surface both — don't silently pick a winner. Prefer the
more authoritative source (CI / lockfile / source code) over the less (README /
comments / naming) and say why; if the conflict is material and unresolved, raise
it as an interview question or `[OPEN]` and lower confidence.

## Rules for avoiding hallucinated claims

1. **No component, dependency, datastore, or data flow asserted as `[FACT]`
   without a `path:line`.** Otherwise it is at best an `[INFERENCE]` with stated
   confidence — or an interview question.
2. **Names are not behavior.** A file called `cache.ts` is evidence of a name,
   not proof of caching — and a directory name is not a confirmed glossary term.
   Term candidates go to the interview, not straight into `CONTEXT.md`.
3. **Do not invent versions, flags, endpoints, config keys, ADRs, or components.**
   Quote them from source or omit them.
4. **Absence ≠ non-existence.** "No tests found in inspected paths" is an
   `[OPEN]`/`[ASSUMPTION]` bounded by what was sampled, not a `[FACT]` that none
   exist.
5. **Prefer "unknown".** An honest open question is more useful to the next agent
   — and to the maintainer being interviewed — than a confident fabrication.
