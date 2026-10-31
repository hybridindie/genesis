---
read_when: "Running an ACD session (/start-session, /end-session, /fix) or writing the spec artifacts for agent-generated work"
---

# Agentic Continuous Delivery (ACD)

Opt-in. A stricter session discipline for agent-generated changes, on top of
`workflow.md`. The pipeline holds agent changes to the same bar as human ones.

## Spec artifacts

Before an agent writes code, these exist and a human has approved them:

| Priority | Artifact | Owner |
|---|---|---|
| 1 | **Intent** — problem statement and hypothesis | Human |
| 2 | **BDD scenarios** — Given/When/Then, in implementation order | Human |
| 3 | **Feature description** — Musts / Must Nots / Preferences / Escalation triggers | Engineering |
| 4 | **Acceptance criteria** — done definition plus known-good cases | Human |
| 5 | Implementation | Agent or human; conforms to all of the above |

When artifacts conflict, the higher one wins and the implementation changes.
An escalation trigger means stop and ask.

## Sessions

- One BDD scenario per session, ending in one commit. `/start-session`
  opens it, `/end-session` closes it.
- Scope constraint for every session: implement this scenario only; note
  improvements in the summary, don't make them.
- An interrupted session ends there; the next one starts from the last commit,
  not from memory.
- While the pipeline is red, the only allowed work is `/fix`.

## MUST

- Agent commits reference the intent (issue) they implement.
- The agent does not write its own acceptance scenarios.
- Human review stays mandatory; passing tests do not prove the intent was met.
- Agent-to-agent handoffs use structured data (JSON schema), not prose.
