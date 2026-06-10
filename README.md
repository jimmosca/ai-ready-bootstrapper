# phase0-bootstrapper

A **day-zero installer of the living convention surface**: it carries an
unknown or legacy repository to the standard conventions — `AGENTS.md` +
`CONTEXT.md` + `docs/adr/` — via **infer → interview → write**, and installs
an **Upkeep Contract** so the surface stays current. It is a convention
bootstrapper for humans and AI alike, not a documentation generator.

> Phase 0 = the Research day before implementation begins. The bootstrapper
> installs the shared language and methodology a team — human and agent — needs
> to work well together. Then it stops.

## What it installs

```
AGENTS.md            # routing + canonical commands + Upkeep Contract
CONTEXT.md           # shared glossary (lazy: only if terms emerge from the interview)
docs/adr/            # durable decisions (lazy: only confirmed, hard-to-reverse calls)
.ai/phase0/scan.json # sensor output for audit / re-bootstrap (internal, read-only)
```

Everything rises to these three standard files, leaves as an issue, or is
dropped. No bespoke artifact tree; no parallel taxonomy to maintain.

The installed **Upkeep Contract** (a section of `AGENTS.md`) defines the
triggers that keep the surface current going forward — most changes trigger
nothing; the contract fires only on decisions, new terms, or verification
changes.

## How to use it

### As a Claude Code skill

The skill is available automatically when Claude Code runs in this repo. To
install it globally or copy it into another project:

```bash
# Claude Code global install:
cp -r .claude/skills/phase0-bootstrapper ~/.claude/skills/

# Portable skill (any agent):
cp -r skills/phase0-bootstrapper <your-agent-skills-dir>/
```

Then open the target repo and invoke: *"Bootstrap this repo."* The skill runs
the three-phase workflow:

1. **Infer** — runs `python scripts/scan.py` (read-only sensor), builds an
   internal draft of facts (`path:line`), inferences (with confidence), and
   open questions. Writes nothing.
2. **Interview** — surfaces open questions and low-confidence inferences to a
   maintainer; answers promote inferences to facts, reveal decisions (→ ADR),
   and capture domain terms (→ `CONTEXT.md`).
3. **Write (lazy, merged)** — seeds only artifacts with real content, in their
   standard locations, via managed markers. Shows a dry-run preview and asks
   for consent before any write.

With `--no-interview`: writes `AGENTS.md` (methodology + canonical commands)
and `docs/adr/0001-adopt-living-convention-methodology.md` from inferred facts,
marks everything unconfirmed as explicit open questions, and skips `CONTEXT.md`
and repo-specific ADRs.

### Optional: run the sensor first

`scripts/scan.py` is a standalone, stdlib-only, LLM-free read-only sensor.
Run it before invoking the skill for a quick inventory, or as part of CI:

```bash
python scripts/scan.py /path/to/repo            # prints JSON, persists .ai/phase0/scan.json
python scripts/scan.py --no-write /path/to/repo  # prints JSON only
```

## Not in scope

**Day-N upkeep is delegated** — the Upkeep Contract installed by the
bootstrapper references ecosystem skills for maintenance:

- [`grill-with-docs`](https://github.com/mattpocock/skills) — stress-test plans
  against the living surface; crystallize new ADRs and terms inline.
- [`to-prd`](https://github.com/mattpocock/skills) — promote open questions to
  a PRD / feature spec.
- [`improve-codebase-architecture`](https://github.com/mattpocock/skills) —
  propose structural changes against the established terminology.

The bootstrapper does not run build/test/install/run/format/codegen commands,
mutate the remote or infra, or perform ongoing maintenance.

## Safety model

The sensor (`scripts/scan.py`) is **read-only and offline** — no LLM, no
network. The write phase is confined to:

- `AGENTS.md`, `CONTEXT.md`, `docs/adr/*` in the target repo — merged via
  `<!-- phase0:start -->…<!-- phase0:end -->` managed markers; prosa outside
  the block is never touched.
- `.ai/phase0/scan.json` — the sensor output artefact.

A dry-run preview + explicit consent gate fires before any write. Secrets are
flagged by location only — their contents are never read, rendered, or printed.
Full rules: [`docs/safety-policy.md`](docs/safety-policy.md).

## Development

```bash
uv sync                              # create .venv and install dev tools
uv run pytest                        # test suite
uv run ruff check .                  # lint
uv run ruff format .                 # format
python scripts/scan.py tests/fixtures/python_fastapi_repo  # try the sensor
```

The formal contract lives in [`docs/`](docs/); see [`AGENTS.md`](AGENTS.md)
for pointers. Status and limitations: [`docs/v0.1-scope.md`](docs/v0.1-scope.md).

## Layout

```
AGENTS.md / CLAUDE.md       # agent guidance → routes to docs/
CHANGELOG.md                # release notes
docs/                       # contract, output schema, safety & evidence policy, scope, demo
scripts/scan.py             # standalone read-only sensor (stdlib-only, no pip install)
pyproject.toml              # uv project + ruff + pytest config
tests/                      # pytest + tests/fixtures/ sample repos
.claude/skills/phase0-bootstrapper/   # Claude Code skill
  SKILL.md                  # orchestrator: three-phase flow, state detection, degradation
  resources/                # output-schema, safety-policy, evidence-policy, templates, example
skills/phase0-bootstrapper/           # portable skill (any agent, self-contained)
  SKILL.md                  # same workflow, self-contained
  resources/                # output-schema, safety-policy, evidence-policy, templates, example
```

## Design lineage

The methodology distills several AI-engineering talks:

- **Dex Horthy (HumanLayer), "No Vibes Allowed"** — Research→Plan→Implement;
  context "dumb zone"; intentional compaction; sub-agent exploration. Phase 0 is
  the *Research* artifact, the highest-leverage step.
- **Eno Reyes (Factory AI), "Making Codebases Agent Ready"** — agents need
  verification loops; solvability ∝ verifiability → the readiness scorecard.
- **Nick Nisi (WorkOS), "Deleted 95% of my skills"** — lean, gotcha-first output;
  more context hurts.
- **Anthropic, "Don't Build Agents, Build Skills"** — skills as simple folders
  with progressive disclosure.
- **Matt Pocock, "Workflow for AI Coding"** + his
  [`skills`](https://github.com/mattpocock/skills) repo — compact imperative
  skills; handoffs reference artifacts instead of duplicating them; living
  convention surface (`AGENTS.md` / `CONTEXT.md` / `docs/adr/`).
- **Michal Cichra, "BDD, ADR, PRD"** — decisions as what / why / **how
  enforced**; capturing shared language for humans and AI alike.
