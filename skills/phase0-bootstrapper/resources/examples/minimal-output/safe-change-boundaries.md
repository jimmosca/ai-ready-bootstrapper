# Safe-Change Boundaries

> Based on scanner signals. When a boundary is unclear, treat it as caution.

## Safe to change
| Area | Why safe | Evidence |
|---|---|---|
| test files | changes are guarded by existing tests | tests/test_app.py |
| docs / README | documentation, low blast radius | README.md |

## Caution — ask / plan first
| Area | Why dangerous | Evidence |
|---|---|---|
| `pyproject.toml` | dependency/build config — affects whole project | pyproject.toml |

## Do-not-touch
- excluded/vendored/build dirs: none present
- lockfiles and generated files (not hand-edited)
