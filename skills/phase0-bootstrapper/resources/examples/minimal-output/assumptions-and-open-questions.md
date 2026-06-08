# Assumptions & Open Questions

> Assumptions come from weak/incomplete signals — verify before relying on them.

## Assumptions
| A# | Assumption | Confirm / refute by | Impact |
|---|---|---|---|
| A1 | Primary language is Python | confirm via maintainer / manifest | medium |
| A2 | The inspected tree is representative (no large excluded source areas) | confirm excluded dirs are vendored/generated only | medium |

## Open questions
| Q# | Question | Why it matters | Priority |
|---|---|---|---|
| Q1 | What is the project's purpose and who owns it? | purpose/ownership cannot be inferred reliably from structure alone | high |
| Q2 | How are changes validated before merge (tests/CI)? | verification surface is the precondition for safe agent work | high |
| Q3 | What is the primary runtime entrypoint and deployment target? | entrypoint detection is limited in this read-only MVP | medium |

## Suggested questions to grill a maintainer
- How do I build, run, and test this locally? What resets the environment?
- Which areas are safe to change vs. landmine territory?
- Where does configuration / secrets come from in each environment?
