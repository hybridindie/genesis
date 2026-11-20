---
name: story-decomposer
description: >
  Turn a ready Epic into story issues a subagent can pick up cold: context,
  Given/When/Then criteria, and an agent-plan block with ownership, verify commands and
  parallel tracks (a contract track first when work shares an interface), validated so
  parallel tracks never touch the same files. Trigger phrases: "decompose this epic",
  "break down this epic into stories", "create stories from this epic", "split this
  epic", "plan the parallel work for this epic". Use when the user has an Epic and wants
  stories and tracks that can be dispatched to parallel subagents.
---

# Story Decomposer

<!--
  The skill itself. OpenCode reads it here; Claude Code loads it through the
  generated .claude/skills/<name>/SKILL.md pointer.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 6.0.0, owner: John D
  invokes: .agents/skills/task-decomposer/SKILL.md,
           .agents/templates/epic/story-shell.md,
           .agents/scripts/plan.py,
           .agents/scripts/tracker.py,
           .agents/evals/story-rubric.md
  doctrine: .agents/doctrine/agent-plan-schema.md,
            .agents/doctrine/parallelization-doctrine.md,
            .agents/doctrine/ai-readable-spec-rules.md,
            .agents/doctrine/source-discipline.md
-->

Turn a ready Epic into story issues that a subagent can pick up cold. Each story
carries an `agent-plan` block with its ownership, verify command and tracks —
the units `wave-dispatcher` hands to parallel subagents. A story body is the
whole brief a subagent gets, so anything it needs to know goes in it.

## Inputs

- Required: the Epic body with a valid `agent-plan` block (a file, or
  `tracker.py get <ref> -o epic.md`).
- Read: `story-shell.md` and the doctrine files above.
- Read: the files and directories named in each story's `owns`, enough to name
  real modules, entry points and test locations.
- Do not read: unrelated code or the whole repository.

## Deterministic Steps

1. **Gate the input.** Run `plan.py validate epic.md`. If it fails, or the Epic
   has no outcome or ACs, stop and send it back to `epic-composer`.
2. **Take the stories from the Epic plan.** Keep every story id, `acs`,
   `depends_on` and `owns`; you refine them, you do not re-slice. If a story
   must change shape, change the Epic plan first and re-validate it.
3. **Write each story body** from `story-shell.md`:
   - the user-story frame (or What/Why for spikes and technical stories);
   - **Context** a subagent with no other knowledge can act on: current
     behaviour, the files involved (named per `ai-readable-spec-rules.md`),
     what exists vs. what is new;
   - Given/When/Then criteria for each Epic AC the story covers, copied into
     `ac_text` with the same labels.
4. **Fill the plan block.** `story`, `epic`, `branch` (`<type>/<issue>-<slug>`),
   `acs`, `ac_text`, `depends_on`, `owns`, `must_not_touch` (the paths parallel
   stories own), `verify`, `context`.
5. **Split into tracks.** One track per independent stream of work inside the
   story, each a subagent in its own worktree:
   - a shared surface inside the story becomes a `kind: contract` track that
     the others depend on;
   - tracks that can run together own disjoint paths (tests go with the code
     they test);
   - an S-sized, single-concern story is one track — say so, don't invent
     parallelism;
   - every track has an exact `verify`.
   Add `integration` (`merge_order`, `verify`) when there is more than one track.
6. **Validate the set and render.** For every story file:
   ```bash
   python3 .agents/scripts/plan.py validate epic.md story-*.md
   python3 .agents/scripts/plan.py sync "$story"
   python3 .agents/scripts/validate_artifact.py --kind story "$story"
   python3 .agents/scripts/plan.py waves epic.md story-*.md
   ```
   Fix the plan on `FAIL`, never the validator.
7. **Quality pass.** When the caller asks for a strict review, or Wave 1 is
   about to be dispatched, apply `.agents/evals/story-rubric.md` (the story
   table to each story, the parallel-plan table to the waves). It advises; it
   never blocks the output.
8. **Publish when asked.** Create each story issue with `tracker.py create`,
   write the returned numbers into the story blocks (`issue`, `branch`) and the
   Epic block (`stories[].issue`), re-sync both, and `tracker.py put` the Epic.
9. **Hand off.** Tracks that need more than one obvious change get tasks from
   `task-decomposer`; the rest are dispatchable as they are.

## LLM Judgment

Use judgment only for:

- writing context a cold subagent can act on;
- where to cut tracks and what each owns;
- whether a shared surface deserves a contract track;
- resolving ownership when the Epic leaves it ambiguous.

Do not invent requirements, file paths, commands, or dependencies. A path you
could not confirm is marked `(new)` in Context.

## Output

- One story body per Epic story, titled `Story N: <outcome>` or
  `story(scope): <outcome>`, each with the generated track table and exactly one
  `agent-plan` block.
- The computed waves across all stories (`plan.py waves`), so the caller sees
  which tracks start first.
- A coverage note: every Epic AC covered by at least one story, or the gap.
- When step 7 ran, the rubric findings per story and for the waves.

## Stop Conditions

- Stop if the Epic plan does not validate; do not decompose an ambiguous outcome.
- Stop if two parallel units would own the same path and neither a contract nor
  a dependency resolves it.
- Stop if an AC cannot be made observable; return it to the acceptance linter.
- Stop if a track cannot name a verify command; ask for the repo's test command.

## Token Budget

- Default: read the Epic, the doctrine files, and the code named in `owns`. Read
  one more file only when ownership or context would otherwise be a guess, and
  say why.
- Target ≤ 400 words of prose per story; the plan block and generated tables do
  not count. Do not restate the Epic.
