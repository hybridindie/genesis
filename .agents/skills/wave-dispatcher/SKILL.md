---
name: wave-dispatcher
description: >
  Execute a planned Epic or story with parallel subagents: start every track whose
  dependencies are done, each in its own git worktree, check each diff stays inside the
  track's owned paths and passes its verify command, merge into the story branch in
  order, and write progress back to the GitHub or Gitea issue. Trigger phrases:
  "dispatch the next wave", "run this epic", "execute the stories in parallel", "start
  the agents on this plan", "work the epic", "kick off wave 1". Use whenever the user
  wants planned Epic/story work implemented by parallel agents, or asks what can run
  next.
---

# Wave Dispatcher

<!--
  The skill itself. OpenCode reads it here; Claude Code loads it through the
  generated .claude/skills/<name>/SKILL.md pointer.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 2.1.0, owner: John D
  invokes: .agents/scripts/dispatch.py,
           .agents/scripts/plan.py
  doctrine: .agents/doctrine/agent-plan-schema.md,
            .agents/doctrine/parallelization-doctrine.md
-->

Execute a planned Epic or story with parallel subagents. `dispatch.py` does
every mechanical step — loading plans from the issues, branches and worktrees,
the scope and verify checks, merge order, conflicts, status written back to the
issues — and prints JSON. You do the two things a script cannot: run the
subagents, and judge whether each one's work does what its brief asked.

Worktrees are what make this safe: parallel subagents never share a working
tree, so their work only meets in a merge that `dispatch.py merge` runs after
the checks pass.

## Inputs

- Required: an Epic or story reference (`#12`, URL) or local body files with
  `agent-plan` blocks.
- Optional: `--max N` concurrent subagents (default 3), `--plan` (dry run),
  `--ship` (open each finished story's PR with ship-pr).
- Read: the JSON `dispatch.py` prints, each brief, each subagent's report and
  each finished track's diff.
- Do not read: the code while a subagent is still writing it.

## Deterministic Steps

Run every command from the repository root; `d=".agents/scripts/dispatch.py"`.

1. **Load.** `python3 $d load --epic <ref>` (or `--story <ref>...`, or
   `--files <paths>` for local bodies). Stop if `ok` is false; report
   `unplanned_stories` — they need story-decomposer before they can run.
2. **Prepare the next wave.** `python3 $d prepare --max <n>`. It refuses a
   dirty checkout, creates each runnable unit's branch and worktree (a story
   that depends on others starts from their finished work), marks it running
   on the issue and writes its brief. It also runs each unit's verify once on
   the untouched worktree: a unit whose verify already passes comes back with
   `weak_check: true`, and its brief asks for a failing test first. With
   `--plan`, run `python3 $d prepare --plan` instead, report the units, their `would_run`
   commands and briefs, and stop. An empty `units` list: go to step 6.
3. **Dispatch in parallel.** In one turn, start one general-purpose subagent
   per unit (Claude Code: the Agent tool; OpenCode: the task tool) whose prompt
   is the unit's brief file, verbatim.
4. **Check each report as it arrives.**
   `python3 $d check <unit>` runs the scope check, the verify command (and
   cleans up what it wrote) and lists commits and findings. Then read the diff
   with the `review` command it prints, against the brief: every task done, the
   ACs actually met, and a contract track implementing the real contract (a
   stub or faked result that only satisfies a weak test is a finding).
   - `ok` and your review passes → `python3 $d merge <unit>`. It enforces
     `merge_order`, and on a conflict aborts and marks the unit blocked.
   - Otherwise → `python3 $d block <unit> --note "<every finding, one clause
     each>"`. Leave the worktree.
5. **Loop** to step 2: merged tracks unblock their dependants and the next
   stories. Stop after 10 rounds.
6. **Integrate finished stories.** For each story in
   `python3 $d report` → `stories_ready_to_integrate`:
   `python3 $d integrate <story> --push` (runs the integration and story
   verify commands, pushes on success). With `--ship`, run ship-pr on the
   branch; never merge without the caller's `--merge`.
7. **Report** from `python3 $d report`.

## LLM Judgment

Use judgment only for:

- reviewing a finished track's diff against its brief and ACs;
- writing the blocker note;
- retrying a blocked track once with a clarified brief, when the blocker was
  missing context rather than a plan or ownership problem.

Do not edit a subagent's code, change ownership, or run the git steps
`dispatch.py` owns by hand — report the failure; the plan gets fixed by
story-decomposer or the human.

## Output

```markdown
Epic: <ref>    Round: <n>    Running: <n>    Done: <n>/<total>    Blocked: <n>

| Unit | Status | Verify | Note |
|------|--------|--------|------|
| S1/contract | done | pass | merged abc123 |
| S1/A | blocked | fail | 2 tests fail in test_routes.py; edits uv.lock |
| S2/main | blocked | weak | verify passed before work; diff adds no test |

Next runnable: <units or none — waiting on …>
Stories integrated: <branches or none>
Blocked worktrees: <paths>
```

With `--plan`: the units that would start, their `would_run` commands and briefs.

## Stop Conditions

- Stop if `load` or `prepare` reports `ok: false` or an `error`.
- Stop dispatching a story after a merge conflict; other stories continue.
- Stop when nothing is runnable and nothing is running.
- Never push to or merge into the default branch; never force-push.

## Token Budget

- Default: the JSON from `dispatch.py`, the briefs, the subagents' reports, and
  each finished track's diff limited to its owned paths.
- Keep the report to the table above plus one line per blocker, ≤ 300 words.
