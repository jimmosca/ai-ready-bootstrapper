# Architecture

> `[INFERENCE]` Structural only. No code-level data-flow or dependency analysis
> was performed (read-only MVP). Names are not behavior.

## Components / modules
| Component | Responsibility | Tag | Confidence | Evidence |
|---|---|---|---|---|
| `src/` | candidate source component | INFERENCE | low | E7 |

## Layering & data flow
`[OPEN]` Not analyzed in this MVP — requires reading code paths.

## Datastores / external services
`[OPEN]` None asserted; would need `path:line` evidence to claim.

## Confidence & limitations
- Confidence: **low**. Components above are inferred from directory names.
- Excluded from inspection: none present.
- A datastore/integration is only claimed when traceable to a `path:line`.
