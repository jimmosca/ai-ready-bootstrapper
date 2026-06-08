# phase0-bootstrapper

An **Agent Skill** that lets a coding agent enter an unknown / legacy repository
in **read-only** mode and compile a reliable **Phase 0 context pack** — the
research foundation a future coding agent starts from.

It does **not** modify the target repo. It inspects, maps, infers cautiously,
captures evidence, flags risks, and produces a structured handoff under
`.ai/phase0/`.

> This is not a documentation generator. It is a **context compiler for coding
> agents**: lean, evidence-backed, with facts / inferences / assumptions / open
> questions kept strictly separate.

## What it produces

```
.ai/phase0/
  manifest.yaml                      # machine-readable index + readiness scorecard
  repo-map.md                        # languages, layout, manifests, generated areas
  commands-and-tooling.md            # build/test/run + verification surface
  entrypoints.md                     # where execution begins
  architecture.md                    # inferred components & data flow
  risk-register.md                   # ranked risks (incl. secrets, test gaps)
  safe-change-boundaries.md          # where it's safe vs. dangerous to edit
  decision-log.md                    # ADR-style: decision / why / how enforced
  assumptions-and-open-questions.md  # the highest-value unknowns
  evidence-map.md                    # every fact → path:line traceability
  agent-handoff.md                   # lean entrypoint for the next agent
```

## Core philosophy

1. **Read-only first** — the only write is the new `.ai/phase0/` folder.
2. **Evidence over vibes** — every fact cites `path:line` or a read-only command.
3. **Separate epistemics** — `[FACT]` / `[INFERENCE]` / `[ASSUMPTION]` / `[OPEN]`.
4. **Lean beats exhaustive** — gotcha lists, not tutorials; more context hurts.
5. **MVP, no overengineering** — eleven solid artifacts, then stop.

## Two ways to use it

### As a CLI

A small Python package (`src/` layout, managed with
[`uv`](https://docs.astral.sh/uv/)) exposes a `phase0` command. `phase0 scan`
runs the full read-only pipeline — walk (path safety, ignored-dir pruning,
≤1 MB reads, project-type/command detection) → compile an evidence-backed
report → write the 11-file pack. The only filesystem write is the output
directory.

```bash
uv sync                 # create the venv and install deps
uv run phase0 --help    # show the CLI
uv run phase0 scan --repo-path /path/to/repo          # writes <repo>/.ai/phase0/
```

`scan` options: `--output-dir DIR` (override the default `<repo>/.ai/phase0/`),
`--dry-run` (inspect and print a summary, write nothing), `--force` (overwrite a
non-empty output dir), `--format text|json` (terminal summary only — never the
generated documents).

### As an agent skill (Claude Code, Codex, …)

Two ready-to-install skill packages ship in this repo:

- `.claude/skills/phase0-bootstrapper/` — Claude Code skill (templates +
  references); available automatically when Claude Code runs in this repo.
- `skills/phase0-bootstrapper/` — portable, self-contained skill: `SKILL.md`
  plus bundled `resources/` (output schema, safety & evidence policies, and a
  real example pack). Copy it into any agent's skills directory.

```bash
# Claude Code, for use on any repo:
cp -r .claude/skills/phase0-bootstrapper ~/.claude/skills/

# Codex / other agents:
cp -r skills/phase0-bootstrapper <your-agent-skills-dir>/
```

Then open the target repo and ask: *"Bootstrap this repo / generate a Phase 0
context pack."* The skill runs the read-only workflow — using the `phase0` CLI
when installed, otherwise the same steps by hand — and writes `.ai/phase0/`.
Review `agent-handoff.md` first; everything else links from there and from
`manifest.yaml`.

## Example

Invocation:

```bash
$ phase0 scan --repo-path ./python_fastapi_repo
```

Terminal summary (`--format text`):

```
phase0 scan summary
  repo path:       /path/to/python_fastapi_repo
  project types:   Python
  output path:     /path/to/python_fastapi_repo/.ai/phase0
  findings:        2
  risks:           0
  open questions:  3
  next step:       Research → Plan: resolve the open questions (esp. how changes are verified) before implementing.

Start at agent-handoff.md. See docs/phase0-contract.md.
```

This writes `.ai/phase0/` with the 11 files. The generated `agent-handoff.md`
(excerpt):

```markdown
# Agent Handoff

## What this repo is
python_fastapi_repo — Python; languages: Python.

## Commands (detected, NOT executed)
Nothing was run — this is a read-only pack.
**Inferred ([INFERENCE], verify before trusting):** pytest, ruff check, ruff format, mypy .

## Biggest unknowns
- What is the project's purpose and who owns it?
- How are changes validated before merge (tests/CI)?
- What is the primary runtime entrypoint and deployment target?
```

A full, unedited example pack lives in
[`skills/phase0-bootstrapper/resources/examples/minimal-output/`](skills/phase0-bootstrapper/resources/examples/minimal-output/).

## Develop

```bash
uv run pytest           # run tests
uv run ruff check       # lint
```

The formal contract the implementation follows lives in [`docs/`](docs/) (see
[`AGENTS.md`](AGENTS.md)).

## Layout

```
AGENTS.md / CLAUDE.md       # agent guidance → routes to docs/
docs/                       # formal contract (phase0/output/safety/evidence)
pyproject.toml              # uv project + ruff + pytest config
src/phase0_bootstrapper/    # cli.py, models.py, scanner.py, renderer.py, safety.py
tests/                      # pytest (+ tests/fixtures/ sample repos)
.claude/skills/phase0-bootstrapper/   # Claude Code skill
  SKILL.md                  # orchestrator: principles, read-only contract, workflow
  references/               # output-spec.md, inspection-playbook.md
  templates/                # lean skeletons for each output file
skills/phase0-bootstrapper/           # portable Codex/agent skill (self-contained)
  SKILL.md                  # operational workflow + safety limits
  resources/                # output-schema, safety-policy, evidence-policy
    examples/minimal-output/  # a real, unedited generated pack
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
  skills; handoffs reference artifacts instead of duplicating them.
- **Michal Cichra, "BDD, ADR, PRD"** — decisions as what / why / **how enforced**.
