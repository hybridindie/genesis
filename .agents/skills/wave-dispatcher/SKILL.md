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
  version: 1.1.0, owner: John D
  invokes: .agents/scripts/plan.py,
           .agents/scripts/tracker.py
  doctrine: .agents/doctrine/agent-plan-schema.md,
            .agents/doctrine/parallelization-doctrine.md
-->

Execute a planned Epic or story: start every track whose dependencies are done,
each in its own git worktree with its own subagent, check that each one stayed
inside its paths and passes its verify command, merge it into the story's
integration branch, and write progress back to the issue. You are the lead —
you schedule, check and merge; subagents write the code.

Worktrees are what make this safe: parallel subagents never share a working
tree, so the only way their work meets is through a merge you run after the
scope and verify checks pass.

## Inputs

- Required: an Epic or story reference (`#12`, URL) or local body files with
  `agent-plan` blocks.
- Optional: `--max N` concurrent subagents (default 3), `--plan` (dry run: print
  what would start and the briefs, change nothing), `--ship` (open each finished
  story's PR with ship-pr).
- Read: `agent-plan-schema.md`, the plan blocks, and subagent reports.
- Do not read: the code the subagents are writing, beyond the diffs you check.

## Deterministic Steps

1. **Preflight.** Require a clean `git status` in the main checkout and an
   up-to-date default branch (`git fetch origin`). Set
   `work=$(git rev-parse --git-common-dir)/agent-plan` and
   `trees=$(dirname "$(git rev-parse --show-toplevel)")/$(basename "$(git rev-parse --show-toplevel)")-tracks`.
2. **Load the plans** into `$work`: the Epic (`tracker.py get <ref> -o
   "$work/epic.md"`) and every story it lists with a real issue number
   (`story-<id>.md`); or just the one story when given a story. Stories still
   `#TBD` are not dispatchable — report them.
3. **Validate and schedule.**
   ```bash
   python3 .agents/scripts/plan.py validate "$work"/*.md
   python3 .agents/scripts/plan.py next "$work"/*.md --max "$max"
   ```
   `next` returns the tracks whose dependencies are `done`, contracts first,
   with no ownership overlap with anything `running`. Empty list: go to step 9.
   With `--plan`, print each unit's worktree command and `plan.py brief`, then stop.
4. **Prepare each unit.** For unit `<story>/<track>` with story branch `$branch`:
   ```bash
   base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
   if ! git show-ref --quiet "refs/heads/$branch"; then
     git branch "$branch" "$base"
     git worktree add "$trees/$story-integration" "$branch"
     # a story that depends on other stories starts from their finished work
     for up in <branches of the stories in depends_on that are not merged yet>; do
       git -C "$trees/$story-integration" merge --no-ff "$up" -m "merge: $up into $branch"
     done
   fi
   git worktree add -b "$branch--$track" "$trees/$story-$track" "$branch"
   python3 .agents/scripts/plan.py status "$work/story-$story.md" --track "$track" --set running
   ```
   The story's PR then contains its upstream stories' commits until those merge
   first — say so in the PR body, and ship stories in wave order.
   Publish the status (`tracker.py put <story-issue> "$work/story-$story.md"`)
   so other sessions see the track is taken.
5. **Dispatch in parallel.** In one turn, start one subagent per unit. Its
   prompt is the output of `plan.py brief "$work/story-$story.md" --track
   "$track"` followed by: `Work only in <worktree path>; cd there first. Your
   branch is <branch>--<track>.` Use a general-purpose subagent with edit and
   shell access (Claude Code: the Agent tool; OpenCode: the task tool).
6. **Check each report as it arrives** — never trust "done" without these.
   Run all three and collect every failure, so one round of feedback fixes
   everything:
   ```bash
   cd "$trees/$story-$track"
   git diff --name-only "$branch"...HEAD > "$work/$story-$track.changed"
   python3 .agents/scripts/plan.py scope "$work/story-$story.md" --track "$track" \
     --changed $(cat "$work/$story-$track.changed")
   <the track's verify command>
   git diff "$branch"...HEAD -- <the track's owns>      # read it, see below
   ```
   - **Scope:** a path outside `owns` fails the track. A generated file the
     plan forgot (a lockfile, a new `__init__.py`) is still a failure — the fix
     is to give it an owner in the plan, not to wave it through.
   - **Verify:** run it even when scope failed, and restore any file the run
     rewrites (`git checkout -- .`) so the evidence stays the agent's.
   - **Review the diff against the brief:** does each task's change exist, does
     it do what the task and its ACs say, and does a contract track implement
     the contract other stories will build on (a stub or a faked result that
     only satisfies a weak test is a failure)? Read only the owned paths.
   - All pass → step 7. Any failure → `status --set blocked --note "<every
     failure, one clause each>"`; keep the worktree; do not merge.
7. **Merge into the story branch** in `integration.merge_order`, never ahead of
   an earlier unmerged track:
   ```bash
   git -C "$trees/$story-integration" merge --no-ff "$branch--$track" -m "merge($story): track $track"
   python3 .agents/scripts/plan.py status "$work/story-$story.md" --track "$track" --set done
   git worktree remove "$trees/$story-$track" && git branch -d "$branch--$track"
   ```
   A merge conflict means the plan's ownership was wrong: `git merge --abort`,
   mark the track blocked, and stop dispatching that story. Publish the status.
8. **Loop.** Go back to step 3: finished tracks unblock their dependants and the
   next stories' contracts. Stop after 10 rounds and report.
9. **Integrate finished stories.** When every track of a story is `done`, run
   `integration.verify` and the story's `verify` in its integration worktree.
   Pass → push the branch; with `--ship`, run ship-pr on it (never merge without
   the caller's `--merge`). Fail → report it as the story's blocker.
10. **Report** and leave blocked worktrees in place.

## LLM Judgment

Use judgment only for:

- reading a subagent's report and diff and deciding whether it is done or
  blocked;
- writing the one-line blocker note;
- whether a blocked track can be retried with a clarified brief (once, and only
  when the blocker was missing context, not a plan conflict).

Do not edit a subagent's code, change a plan's ownership, or reorder merges to
get past a failure — report it; `story-decomposer` or the human fixes the plan.

## Output

```markdown
Epic: <ref>    Round: <n>    Running: <n>    Done: <n>/<total>    Blocked: <n>

| Unit | Status | Verify | Note |
|------|--------|--------|------|
| S1/contract | done | pass | merged abc123 |
| S1/A | blocked | fail | 2 tests fail in test_routes.py |

Next runnable: <units or none — waiting on …>
Stories ready to ship: <branches or none>
Blocked worktrees: <paths>
```

With `--plan`: the units that would start, their worktree commands and briefs.

## Stop Conditions

- Stop if the main checkout is dirty or the plans do not validate.
- Stop dispatching a story after a merge conflict or a scope violation; other
  stories continue.
- Stop when nothing is runnable and nothing is running.
- Never push to or merge into the default branch; never force-push.

## Token Budget

- Default: read the plan blocks, the subagents' reports, and each finished
  track's diff limited to its owned paths.
- Do not read the code while a subagent is still writing it, or outside the
  track's owned paths.
- Keep the report to the table above plus one line per blocker, ≤ 300 words.
