---
description: ACD pipeline-restore session — diagnose and fix a failing pipeline before any feature work resumes
---

Restore pipeline health. While the pipeline is red, the only valid work is restoring green. Feature work does not resume until this session completes.

## Steps

1. **Identify the failure** — run the failing pipeline stage locally and collect the exact error output. Do not guess; read the output.

2. **Classify the failure**:
   - **Regression from latest commit** — the most recent commit broke something. Identify which commit introduced the failure.
   - **Pre-existing failure** — the failure existed before the current session. Confirm by checking out the prior commit.
   - **Environmental failure** — a dependency, service, or configuration issue unrelated to code changes. Escalate to the user if confirmed environmental.

3. **Scope the fix** — state explicitly what must change to restore green. If the fix requires touching code outside the failing scenario, note that as a concern and get confirmation before proceeding.

4. **Implement the minimal fix** — change only what is required to make the pipeline green. Do not refactor, rename, or improve anything else in this session.

5. **Verify green** — run `preflight` and confirm all checks pass.

6. **Commit the fix** separately from any feature work:
   ```
   fix(<scope>): restore pipeline — <one sentence describing what broke and what fixed it>
   ```

7. **Resume the interrupted feature session** — once the pipeline is green, run `start-session` to re-initialize the feature context cleanly. Do not continue the interrupted session from memory.

## Output

```
Pipeline restored.
Root cause: <one sentence>
Fix: <one sentence>
Commit: <sha>
Pipeline status: green
Ready for: start-session
```
