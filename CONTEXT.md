# CONTEXT.md

Shared language for this repo — the words we use and what they mean here, so
humans and agents talk about the same thing. **Glossary only:** definitions, not
mechanics. How we actually work (the loop, the triggers, the commands) lives in
[`AGENTS.md`](AGENTS.md); decisions live in [`docs/adr/`](docs/adr/). When a term
is added or redefined, update it here in the same change (see the Upkeep
Contract in `AGENTS.md`).

## Terms

### phase0-bootstrapper
The day-zero installer that takes an unknown repo to the living convention
surface by infer → interview → write. "Phase 0" = the Research phase / day zero;
"bootstrapper" = an installer, not a maintainer.
_Avoid:_ generator, documentation generator, documenter.

### Living convention surface
The deliverable: the living set of `CONTEXT.md` + `docs/adr/` + `AGENTS.md` that
day-zero seeds and agents keep current.
_Avoid:_ context pack, the pack.

### Upkeep Contract
The clause in `AGENTS.md` that obliges agents to keep the living convention
surface current. Trigger-driven, not "any change".
_Avoid:_ maintenance docs, changelog.

### Day-zero install
The bootstrapper's one job: install the surface, then stop. Day-N upkeep belongs
to the ecosystem skills.
_Avoid:_ ongoing maintenance.

### RPI+Verify loop
This repo's work loop — Research → Plan → Implement → Verify — with weight on the
extremes.
_Avoid:_ vibe coding, strict SDD-always.

### Verify gate
The hard rule that a change is not done until the canonical commands pass.
Reliability over autonomy.
_Avoid:_ "done" without verifying.

### Canonical commands
The copy-pasteable build/test/lint/run/verify commands in `AGENTS.md`; the
center of gravity for the Verify gate.
_Avoid:_ "how to build" in prose.

### Blast radius
The size of a change's impact; it grades how much Plan a change earns and when to
stop and ask.
_Avoid:_ risk (too generic).

### Sensor
The deterministic, LLM-free script (`scripts/scan.py`) that inspects a target
repo read-only and emits the internal `scan.json` — signals and candidates, not
judgements. Same input, same output; the agentic skill interprets what it reports.
_Avoid:_ scanner, generator.

### Glossary candidate
A name the Sensor surfaces — a directory, a declaration, a README heading — that
might be a domain term. A candidate carries sources, not a meaning: only the
interview can confirm it into `CONTEXT.md`. Names are not behavior.
_Avoid:_ glossary term, definition.

### Verbatim mirror
`.claude/skills/phase0-bootstrapper/` as a byte-identical, regenerated (never
hand-edited) copy of the portable `skills/phase0-bootstrapper/` source. See
ADR-0004.
_Avoid:_ sync, fork.

### Localization transform
The bounded rewrite applied to a contract document (or the Sensor) when it is
copied from `docs/` / `scripts/` into the skill's portable `resources/`: rewrite
or remove only what does not resolve from `resources/`, change nothing else. See
ADR-0005.
_Avoid:_ drift, fork.
