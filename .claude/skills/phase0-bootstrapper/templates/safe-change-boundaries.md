# Safe-Change Boundaries

> Guardrails for the next agent: where editing is low-risk vs. where to stop and
> ask. Evidence-backed. Lacking verification coverage = treat as dangerous.

## Safe to change
<!-- Well-tested, isolated, internal. -->
| Area | Why safe | Evidence |
|---|---|---|
|  |  | E# |

## Dangerous — ask / plan first
<!-- Public APIs, DB migrations, generated/vendored code, shared config,
     auth/security, untested hot paths. -->
| Area | Why dangerous | Evidence |
|---|---|---|
|  |  | E# |

## Do-not-touch
<!-- Generated, vendored, lockfiles, build output — edit the source instead. -->
