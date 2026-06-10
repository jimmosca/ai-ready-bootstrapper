# Inspection playbook — signals by repo type

Use these signals during the **Infer** phase to build the internal draft. Feed
them to `scripts/scan.py` (sensor) or apply manually when the sensor is absent.
Read-only throughout — cite `path:line`; never run anything.

## First, fingerprint the repo
- `git ls-files | wc -l`, language mix (extensions), monorepo markers
  (`pnpm-workspace.yaml`, `nx.json`, `turbo.json`, `lerna.json`, Go workspaces,
  Cargo workspaces, Bazel `WORKSPACE`).
- Manifests reveal the ecosystem; lockfiles reveal pinned reality.

## Manifests, commands & verification by ecosystem
- **Node/TS**: `package.json` (`scripts`, `engines`, `packageManager`),
  lockfile (npm/yarn/pnpm/bun), `tsconfig.json`, `eslint`/`biome`, test runner
  (`vitest`/`jest`/`playwright`). Entrypoints: `bin`, `main`/`module`/`exports`,
  framework bootstraps (Next `app/`/`pages/`, Express/Nest `main.ts`).
- **Python**: `pyproject.toml`/`setup.cfg`/`requirements*.txt`, `poetry.lock`/
  `uv.lock`, `tox.ini`/`noxfile`, `pytest.ini`, `ruff`/`flake8`/`mypy`.
  Entrypoints: `[project.scripts]`, `__main__.py`, `manage.py`, ASGI/WSGI app,
  Celery, FastAPI/Flask app objects.
- **Go**: `go.mod`, `Makefile`, `main` packages (`func main`), `*_test.go`.
- **JVM**: `pom.xml`/`build.gradle(.kts)`, `mvnw`/`gradlew`, Spring Boot
  `@SpringBootApplication`, `src/test`.
- **Rust**: `Cargo.toml`/`Cargo.lock`, `src/main.rs` vs `lib.rs`, `tests/`.
- **Ruby/PHP/.NET/etc.**: `Gemfile`, `composer.json`, `*.csproj`/`*.sln`.

## Cross-cutting sources of truth
- `Makefile`/`Taskfile`/`justfile` — canonical commands.
- CI: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, CircleCI, Azure —
  the **real** build/test/deploy steps and gates (treat as `[FACT]`).
- Containers: `Dockerfile`, `docker-compose*.yml`, `.devcontainer/` — env setup.
- Config & secrets: `.env.example`, `config/`, `*.tfvars.example`. Note secret
  *presence* and risk; never read values.
- Docs: `README`, `CONTRIBUTING`, `docs/`, `ADR*/adr/`, `CHANGELOG`.

## Data / ETL repos
- Pipeline defs: Airflow DAGs, Dagster, Prefect, dbt (`dbt_project.yml`,
  `models/`), Spark jobs, SQL migrations (`alembic`, `flyway`, `prisma/migrations`).
- Datastores & schemas, connection config, scheduling, data contracts.

## AI / ML repos
- Training/eval/inference scripts; experiment config (Hydra, YAML); notebooks
  (`*.ipynb`); model/data versioning (DVC, MLflow, W&B, HF); checkpoints &
  large artifacts (Git LFS); GPU/CUDA assumptions; prompt/eval suites.

## Infra repos
- Terraform/Pulumi/CloudFormation, Helm/Kustomize/`k8s/`, Ansible. Note
  environments, state backends, and blast radius.

## Risk smells (read-only)
- Committed secrets/keys, `.env` with real values, private keys, tokens in code.
- No tests / tiny test dir vs. large `src`; no CI; failing-looking config.
- Unpinned or wildcarded deps; very old/deprecated deps; many TODO/FIXME/HACK.
- Huge binaries/data in git; generated code committed without markers; dead code.
- Tight coupling to a local/personal environment (hardcoded paths, ports, hosts).

## No verification loop found?
If the scan finds **no** test/lint/typecheck/CI loop, do not silently skip the
Verify rule. Instead, `AGENTS.md` must say so explicitly: "no automated
verification found; high-risk changes; verify manually by [X]; **setting up
verification is the first recommended task**." This is open question #1, not a
dropped rule.
