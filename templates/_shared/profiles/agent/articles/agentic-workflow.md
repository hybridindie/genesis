---
read_when: "Running multi-step agent delivery or changing the ACD workflow"
paths:
  - "**/*"
---

# Agentic Continuous Delivery (ACD)

An agent-generated change must meet or exceed the same quality bar as a human-generated change. The pipeline does not care who wrote the code.

## ACD Constraints

1. Explicit, human-owned intent exists for every change
2. Intent and architecture are represented as delivery artifacts
3. All delivery artifacts are versioned and delivered together with the change
4. Intended behavior is represented independently of implementation
5. Consistency between intent, tests, implementation, and architecture is enforced
6. Agent-generated changes must comply with all documented constraints
7. Agents implementing changes must not promote those changes to production
8. While the pipeline is red, agents may only generate changes restoring pipeline health

## Artifact Authority (Conflicts: higher wins, implementation changes — not the intent)

| Priority | Artifact | Owned By |
|----------|----------|----------|
| 1 | Intent Description | Human — problem statement + hypothesis |
| 2 | User-Facing Behavior | Human — BDD scenarios, observable outcomes |
| 3 | Feature Description | Engineering — Musts / Must Nots / Escalation Triggers |
| 4 | Acceptance Criteria | Human — done definition + known-good test cases |
| 5 | System Constraints | Team — global non-functional requirements |
| 6 | Implementation | Agent/Human — lowest authority; conforms to all above |

When an agent encounters an escalation trigger in the feature description, it stops and asks — it does not decide autonomously.

## Session Discipline

One BDD scenario. One session. One commit. Full session procedure: `/start-session`, `/end-session`, `/fix`.

**Scope constraint — required in every implementation session system prompt:**
> Implement the behavior described in this scenario and only that behavior. Note any improvements in your summary but do not make them. Cleanup happens in a separate session with its own commit.

Any session interruption is a session boundary. The next session starts from the last committed state only.

## MUST

- Define all four spec artifacts (intent, BDD scenarios, feature description, acceptance criteria) **before** any code generation
- One BDD scenario per session; sessions end at a commit
- Tag every agent-generated commit with agent identity and intent description reference (provenance)
- Store skills, system prompts, and agent configuration in version control — they are delivery artifacts
- Human review is mandatory until expert validation agents complete ≥20 calibration cycles

## ANTI-PATTERNS

- Agent defines its own test scenarios (tests shaped to pass code, not verify intent)
- Session spans a commit boundary (mixed context, contaminated bisect trail)
- Agent resumes without context reset (start from committed state, not session memory)
- Tests pass therefore change is correct (tests ≠ intent alignment; human review remains required)
- Agent improves code outside session scope (schedule cleanup as a separate committed session)
- No provenance tracking (cannot audit failures or tighten constraints over time)
- Natural language at agent-to-agent interfaces (use JSON schemas; prose causes cascade parse failures)
- Rules or project context file used for procedures (procedures belong in skills/commands, loaded on demand)
