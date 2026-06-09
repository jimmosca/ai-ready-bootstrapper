# 0003 — GitHub working methodology (lean spine + detection override)

- **Status:** Accepted
- **Date:** 2026-06-10

## Context

[ADR-0001](0001-adopt-living-convention-methodology.md) adopted the work loop;
working through GitHub needs a convention too. We base it on **Matt Pocock's**
issue-centric, AFK-oriented workflow for simplicity (skills: `to-prd`,
`to-issues`, `triage`, `request-refactor-plan`). But his full system — a 7-state
triage machine, a label taxonomy, an `.out-of-scope/` knowledge base, agent
briefs — is heavier than we want to impose by default.

## Decision

Install a **lean spine**, and **adopt the repo's own system when it has one**.

Spine (the default when the repo has no convention of its own):

- The **issue is the unit of work**, each a **tracer-bullet vertical slice**
  (thin, end-to-end, demoable); prefer **AFK** over HITL.
- **Tiny commits that keep the repo green** (Fowler); **branch per issue**
  (`<type>/<issue>-<slug>`); **one PR per slice** (`Closes #N`);
  **squash-merge per slice** (tiny commits live on the branch for review/bisect,
  squashed on `main` for a clean history).
- Commit messages: **Conventional Commits**.
- The **Verify gate** (ADR-0001) must pass before merge.
- Minimal labels: **`ready-for-agent`** + **`needs-info`** only.

The richer machinery (PRD→issues pipeline, full triage state machine,
`.out-of-scope/`, agent briefs) is **referenced as available skills**, not
mandatory process.

**Detection override.** If the repo already has any of `CONTRIBUTING.md`, a PR
template, an established label taxonomy, `CODEOWNERS`, a branch-naming
convention, or a commit convention (Conventional Commits / commitlint), **adopt
it** and record the deviation; fill only the gaps with the defaults above. Never
rewrite an existing convention.

**Day-zero documents and offers; it does not mutate the remote or infra.**
Existing labels are adopted; absent labels are not auto-created — the bootstrapper
leaves a consented snippet instead (below). Verify-before-merge is enforced by CI
/ branch protection where present; where absent, by local discipline, and
"set up CI" becomes the #1 recommended task (ADR-0001 consequence). The issue
tracker defaults to GitHub Issues with abstract wording ("the project's issue
tracker") for portability; another detected tracker is pointed at conceptually,
not integrated.

## Why this is an ADR

Hard-ish to reverse once the convention forms, **surprising** (we deliberately do
*not* install the full Pocock system), and a real trade-off (simplicity and
low noise vs. a more powerful AFK pipeline from day one).

## Label snippet (run only with consent)

```sh
gh label create ready-for-agent -c '#0E8A16' -d 'Fully specified; an AFK agent can pick it up'
gh label create needs-info      -c '#FBCA04' -d 'Blocked on more information from the reporter'
```
