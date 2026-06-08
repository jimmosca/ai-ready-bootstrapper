# Changelog

All notable changes to `phase0-bootstrapper` are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-08

First MVP release. Read-only repository analysis that compiles a Phase 0 context
pack for coding agents. See [`docs/v0.1-scope.md`](docs/v0.1-scope.md) for the
full scope and limitations.

### Added

- **`phase0` CLI** with a `scan` command: `--repo-path`, `--output-dir`,
  `--dry-run`, `--force`, and `--format text|json`. Writes the pack only on a
  real (non-dry-run) scan.
- **Read-only scanner**: size-limited, symlink-safe directory walk with
  cache/vendored/build-dir pruning; detection of languages, project types
  (Python, Node/TypeScript, Terraform/IaC, dbt, data pipeline, mixed repo),
  important files, and commands (npm scripts / Makefile targets as `[FACT]`,
  pyproject tooling as `[INFERENCE]` with confidence). No command is executed.
- **Renderer** producing the 11-file pack at `<repo>/.ai/phase0/` (`manifest.yaml`
  + 10 markdown files) per [`docs/output-schema.md`](docs/output-schema.md),
  with an evidence ledger and `Phase0Report.validate()` that fails on any
  dangling `E#` reference.
- **Safety layer**: refuses system/home roots and the repo root as targets;
  validates the output dir (only `<repo>/.ai/...` or a path outside the repo);
  skips secret-bearing files, binaries, oversize (>1 MB) files, and symlinks
  when reading. Secret files are recorded by location only — never read or
  printed.
- **Agent Skill packaging**: a Claude Code skill (`.claude/skills/`) and a
  portable, self-contained skill (`skills/phase0-bootstrapper/`) with bundled
  resources and a real example pack.
- **Fixture repositories** under `tests/fixtures/` (FastAPI, Node/TypeScript,
  Terraform, dbt, mixed data/AI) for static-analysis tests — no installs needed.
- **Documentation**: contract, output schema, safety policy, and evidence policy
  under `docs/`, plus [`docs/v0.1-scope.md`](docs/v0.1-scope.md) and
  [`docs/demo.md`](docs/demo.md).

### Notes

- **Zero runtime dependencies** (Python standard library only).
- **No LLM calls and no external services** — detection is deterministic.
