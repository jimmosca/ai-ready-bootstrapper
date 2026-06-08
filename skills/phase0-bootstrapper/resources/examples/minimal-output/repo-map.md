# Repo Map

## Purpose
See `README.md` (evidence E5). `[OPEN]` purpose text not extracted in this MVP.

## Languages
`[FACT]` Python — by file extension over the read-only walk.

## Top-level layout
- `.github`
- `Dockerfile`
- `README.md`
- `pyproject.toml`
- `src`
- `tests`

## Important files
| Category | Path | Evidence |
|---|---|---|
| dockerfile | `Dockerfile` | E3 |
| github_actions | `.github/workflows/ci.yml` | E4 |
| python_manifest | `pyproject.toml` | E2 |
| readme | `README.md` | E5 |
| tests | `tests/test_app.py` | E6 |

## Likely project types
`[INFERENCE]` Python (confidence: low–medium).

## Unclear areas
- Runtime behavior, data flow, and deployment are not inferable from structure alone.
- Excluded from the walk: none present.
