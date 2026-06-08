# Commands & Tooling

> Nothing was executed (read-only). `fact` = found verbatim in a manifest;
> `inference` = inferred from tooling presence (carries confidence).

## Package manager / runtime
- Package manager: Python (pyproject/pip — `[INFERENCE]` lockfile not inspected)
- Languages: Python

## Detected commands
| Category | Command | Source | Tag | Confidence | Evidence |
|---|---|---|---|---|---|
| test | `pytest` | `pyproject.toml` | inference | medium | E2 |
| lint | `ruff check` | `pyproject.toml` | inference | medium | E2 |
| format | `ruff format` | `pyproject.toml` | inference | medium | E2 |
| typecheck | `mypy .` | `pyproject.toml` | inference | medium | E2 |

## Infrastructure / CI tools
- Docker
- GitHub Actions
