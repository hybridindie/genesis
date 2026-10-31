---
description: Initialize an ACD implementation session — validate spec artifacts, assemble session context, prepare for one BDD scenario
---

Begin an ACD implementation session. One session implements exactly one BDD scenario.

## Steps

1. **Verify spec artifacts exist and are human-approved** before loading any code:
   - Intent description (problem statement + hypothesis)
   - BDD scenarios (complete set for this feature, in implementation order)
   - Feature description (Musts / Must Nots / Preferences / Escalation Triggers)
   - Acceptance criteria (done definition + test cases with known-good outputs)
   - If any artifact is missing or unapproved, stop and report which artifact is needed.

2. **Identify the scenario for this session** — the next unimplemented BDD scenario in the ordered list. Confirm with the user if ambiguous.

3. **Assemble session context in this order** (stable first for cache efficiency):
   - Agent rules (already present)
   - Project context file (already present)
   - Feature description for this feature
   - The one BDD scenario being implemented this session
   - Relevant existing files the scenario touches
   - Prior session summary (if any)

4. **Exclude from context:**
   - Full conversation history from previous sessions
   - Scenarios not being implemented this session
   - Unrelated system context or verbose rationale

5. **Confirm scope constraint is active** — state it explicitly before generating any code:
   > Implement the behavior described in this scenario and only that behavior. If you encounter code that could be improved, note it in your summary but do not make changes to it. Any refactoring, renaming, or cleanup must happen in a separate session with its own commit.

6. **Confirm pipeline is green** before beginning. If the pipeline is red, run `fix` first — this is a restore session, not a feature session.

7. **Report ready**: state the scenario name, the files expected to change, and the acceptance criteria that must pass.

## Output

```
Session ready.
Scenario: <scenario name>
Files in scope: <list>
Acceptance criteria: <list>
Pipeline status: green
```
