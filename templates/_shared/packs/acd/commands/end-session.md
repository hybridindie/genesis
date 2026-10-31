---
description: Close an ACD implementation session — validate all gates, write context summary, and commit
---

Close the current ACD implementation session. Run after the acceptance test for this scenario passes.

## Steps

1. **Run preflight checks** — run `preflight`. If any check fails, fix it before continuing. Do not commit with a failing gate.

2. **Verify acceptance criteria** — confirm every acceptance criterion for this session's scenario passes. If any fail, this session is not done.

3. **Verify no out-of-scope changes** — review the staged diff. If files outside the scenario scope were modified, unstage them and explain what needs a separate session.

4. **Write the context summary** — a factual paragraph (100–150 words max) for future sessions:
   - Which scenario was implemented
   - Which files were created or modified and what each does
   - Any concerns or follow-up items noted (but not acted on) during the session
   - Pipeline status: green

   Template:
   ```
   Session N implemented Scenario X (<scenario name>).

   Files created/modified:
   - <file> — <one sentence: what it does>

   Concerns noted (not acted on):
   - <concern> — scheduled as separate session

   Pipeline is green.
   ```

5. **Commit** with message referencing the scenario:
   ```
   feat(<scope>): <imperative description of the scenario behavior> (closes #<issue>)
   ```

6. **Report done**: scenario name, commit SHA, and any follow-up sessions needed.

## Output

```
Session N complete.
Scenario: <name>
Commit: <sha>
Follow-up sessions needed: <list or "none">
```
