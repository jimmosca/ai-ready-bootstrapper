# 0002 — Do not enforce BDD

- **Status:** Accepted
- **Date:** 2026-06-09

## Context

[ADR-0001](0001-adopt-living-convention-methodology.md) makes Verify a hard rule.
A natural follow-up is whether to standardize on **BDD/Gherkin** (Cucumber,
behave, `*.feature`) as the acceptance-test format — especially since
behaviour/decision capture is part of the lineage we drew on.

## Decision

Do **not** enforce BDD. The Verify gate stays **framework-agnostic**. If a repo
already uses a BDD framework, the canonical commands run it; the bootstrapper
never introduces it.

## Why

BDD is two things: the **idea** (specify behaviour by example, in shared
language, executable) and the **tooling** (Gherkin + step definitions). The
idea's substance is already covered by our surface — shared language in
`CONTEXT.md`, the conversation in `grill-me` / Plan, executable acceptance in the
Verify gate. The tooling adds triple maintenance (scenario → step regex → code)
and brittleness, and its historical justification — non-technical stakeholders
co-authoring tests — largely evaporates in an agent-driven flow where a human
grills the agent directly. BDD-format earns its keep only in
contractual/regulated domains where stakeholders actually read the scenarios;
that is a minority.

## Why this is an ADR

A deliberate **rejected alternative**, recorded so no one re-proposes Cucumber in
six months assuming it was simply overlooked. BDD is a common default (surprising
to omit), conventions are hard to reverse once they form, and there is a real
trade-off.
