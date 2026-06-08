# Output Schema

The 11 files of `<target-repo>/.ai/phase0/`. For each: **Purpose**, **Required
sections**, **Must not include**, **Skeleton**. Skeletons are the canonical
minimum; working copies live in `.claude/skills/phase0-bootstrapper/templates/`.

Conventions (see [evidence-policy.md](evidence-policy.md)): tag claims
`[FACT] / [INFERENCE] / [ASSUMPTION] / [OPEN]`; facts cite an evidence ID `E#`
that resolves in `evidence-map.md`. Keep every file lean and gotcha-first.

---

## manifest.yaml
- **Purpose:** machine-readable index + readiness scorecard; parseable without
  the prose files. The first thing an agent loads.
- **Required sections:** `schema_version`, `generated_at`, `generator`, `repo`
  (name/root/vcs/head_commit/file_count/languages), `files` (10 artifacts with
  `confidence` + `summary`), `agent_readiness` (8 dimensions), `coverage`
  (inspected / skipped_or_sampled / unknown).
- **Must not include:** prose narrative, secret values, claims without a backing
  file.
- **Skeleton:**
```yaml
schema_version: "0.1"
generated_at: ""
generator: phase0-bootstrapper
repo: { name: "", root: "", vcs: git, head_commit: "", file_count: 0, languages: [] }
files:
  - { path: repo-map.md, confidence: low, summary: "" }
  # ...one entry per markdown artifact
agent_readiness:
  build: { status: unknown, note: "" }   # present|partial|absent|unknown
  # test, lint_format_typecheck, ci_gates, env_setup_reset, run_locally, docs_specs, correctness_signal
coverage: { inspected: [], skipped_or_sampled: [], unknown: [] }
```

## repo-map.md
- **Purpose:** what the repo physically is — languages, layout, manifests,
  generated/vendored areas.
- **Required sections:** Languages; Top-level layout (annotated tree, not a full
  dump); Key directories; Manifests & lockfiles; Generated/vendored/build output;
  Notable/large files.
- **Must not include:** full file listings, architectural interpretation
  (belongs in architecture.md), prose.
- **Skeleton:**
```markdown
# Repo Map
## Languages
## Top-level layout
## Key directories       | dir | purpose | tag | E# |
## Manifests & lockfiles
## Generated / vendored / build output
## Notable / large files
```

## architecture.md
- **Purpose:** the inferred system model — components, data flow, stores,
  integrations.
- **Required sections:** Components/modules; Layering & data flow; Datastores;
  External services/integrations; Cross-cutting concerns; Confidence & gaps.
- **Must not include:** unevidenced claims presented as fact; diagrams not backed
  by evidence; speculation (push to assumptions-and-open-questions.md).
- **Skeleton:**
```markdown
# Architecture
## Components / modules   | component | responsibility | tag | E# |
## Layering & data flow
## Datastores
## External services / integrations
## Cross-cutting concerns
## Confidence & gaps
```

## entrypoints.md
- **Purpose:** where execution begins — the "where do I start reading" map.
- **Required sections:** a table of entrypoints (path:line, type, trigger, what
  it does, evidence); Notes.
- **Must not include:** non-entrypoint files, architectural narrative.
- **Skeleton:**
```markdown
# Entrypoints
| Entrypoint | Type | Trigger | What it does | Evidence |
|---|---|---|---|---|
## Notes
```

## commands-and-tooling.md
- **Purpose:** how to build/test/run/verify; the verification surface.
- **Required sections:** Build; Test; Lint/Format/Typecheck; Run/Serve;
  Deploy/Release (each: command, source `path:line`, `[FACT]`/`[INFERENCE]`);
  Verification surface (framework, coverage, CI gates, env setup/reset, gaps).
- **Must not include:** commands presented as verified when they were not run
  (unrun = `[INFERENCE]`); invented flags.
- **Skeleton:**
```markdown
# Commands & Tooling
## Build / Test / Lint / Run / Deploy   | command | source | tag |
## Verification surface  (framework, coverage, CI gates, env reset, gaps)
```

## decision-log.md
- **Purpose:** ADR-style record of decisions inferred from the code.
- **Required sections:** Inferred decisions (each: Decision · Why (inferred) ·
  How enforced · evidence · confidence); Existing decision artifacts found
  (ADRs/PRDs/specs by path).
- **Must not include:** prescriptive new decisions; "why" stated as fact when it
  is inferred.
- **Skeleton:**
```markdown
# Decision Log (ADR-style)
### D1 — <decision>
- Decision / Why (inferred) / How enforced / Evidence: E#
## Existing decision artifacts found   | doc | topic | path |
```

## assumptions-and-open-questions.md
- **Purpose:** the highest-value unknowns, framed to be resolved by a human/agent.
- **Required sections:** Assumptions (id, assumption, confirm/refute by, impact
  if wrong); Open questions (id, question, why it matters, priority); Suggested
  questions to grill a maintainer.
- **Must not include:** resolved facts, low-value trivia.
- **Skeleton:**
```markdown
# Assumptions & Open Questions
## Assumptions       | A# | assumption | confirm/refute by | impact |
## Open questions    | Q# | question | why it matters | priority |
## Suggested questions to grill a maintainer
```

## risk-register.md
- **Purpose:** ranked risks that constrain safe work.
- **Required sections:** Risk table (id, risk, category, evidence, likelihood,
  impact, note); Top 3 risks for the next agent.
- **Must not include:** secret values (record existence + location only);
  unranked dumps.
- **Skeleton:**
```markdown
# Risk Register
| ID | Risk | Category | Evidence | Likelihood | Impact | Note |
## Top 3 risks for the next agent
```

## safe-change-boundaries.md
- **Purpose:** guardrails — where editing is low-risk vs. where to stop and ask.
- **Required sections:** Safe to change; Dangerous — ask/plan first;
  Do-not-touch (generated/vendored/lockfiles/build output).
- **Must not include:** advice without evidence; blanket "everything is safe".
- **Skeleton:**
```markdown
# Safe-Change Boundaries
## Safe to change        | area | why safe | E# |
## Dangerous — ask first | area | why dangerous | E# |
## Do-not-touch
```

## agent-handoff.md
- **Purpose:** the lean entrypoint for the next agent. Write last.
- **Required sections:** What this repo is; Start here; Verified commands
  (`[FACT]` only); Agent-readiness scorecard; Top risks; Safe-change rules;
  Biggest unknowns; Suggested next step (RPI).
- **Must not include:** duplication of other files (reference them by path);
  unverified commands in "verified"; secrets/PII.
- **Skeleton:**
```markdown
# Agent Handoff
## What this repo is
## Start here
## Verified commands        (only [FACT])
## Agent-readiness scorecard (link manifest.yaml)
## Top risks / ## Safe-change rules / ## Biggest unknowns
## Suggested next step       (Research → Plan before Implement)
```

## evidence-map.md
- **Purpose:** traceability index; single source of truth for evidence IDs.
- **Required sections:** a table `E# | claim (short) | source (path:line or
  command) | type`.
- **Must not include:** claims without a source; duplicated narrative.
- **Skeleton:**
```markdown
# Evidence Map
| ID | Claim (short) | Source (path:line or command) | Type |
|---|---|---|---|
```
