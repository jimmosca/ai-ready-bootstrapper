# 0005 — Localization adapter for portable resource files

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

The contract documents (`output-schema.md`, `safety-policy.md`,
`evidence-policy.md`) and the sensor (`scripts/scan.py`) each exist twice: the
canonical copy in `docs/` (and `scripts/`) and a portable copy in
`skills/phase0-bootstrapper/resources/` that ships inside the skill. The
localized set is `{output-schema,safety-policy,evidence-policy}.md` plus
`resources/scan.py`. The copies are **not byte-identical**: links and paths
that resolve from `docs/` (e.g. `adr/0002-no-enforcing-bdd.md`,
`scripts/scan.py`, the dogfood example pointer) would dangle from inside
`resources/`, so the portable copy rewrites or removes them; `resources/scan.py`
diverges from `scripts/scan.py` only by an added header line identifying it as
the bundled, localized copy.

## Decision

Divergence between the two copies is **allowed but bounded**: the portable copy
may differ from `docs/` (and `scripts/scan.py`) only by the *localization
transform* — rewrite or remove anything that does not resolve from
`resources/`. The exact allowed divergence is locked in by a canonical-anchored
substitution allowlist: a pytest applies the registered (old→new) substitutions
to each `docs/` (and `scripts/scan.py`) source and asserts the result equals the
`resources/` copy; any other difference fails. Because the comparison is
anchored to the canonical source, an unmirrored canonical edit breaks the test.

## Why

Converging to byte-identical copies would degrade both files — `docs/` would
lose clickable repo-relative links, the portable copy would lose its bundled
example pointer. But unbounded divergence is how drift starts: it already
happened once (P3→P4 window), and the dangerous vector is a `docs/`
safety-policy edit that narrows the write set without being mirrored — the
deployed skill silently keeps the weaker contract. A golden fixture (a
snapshot of the portable copy) would not catch this: the snapshot only
compares the portable copy against its own prior version and stays green even
when the canonical source it was supposed to track changes underneath it. The
substitution allowlist avoids that blind spot by anchoring the assertion to
the canonical source on every run, so the divergence stays explicit and
reviewable — touching either side, or letting them drift apart beyond the
registered substitutions, breaks the test.

## Why this is an ADR

A future reader comparing the two copies will see divergent files and assume
drift; this records that the divergence is deliberate and machine-bounded. The
substitution allowlist locks in the localization pattern (hard to reverse
casually), and byte-identical convergence was a genuine alternative rejected
for specific reasons.
