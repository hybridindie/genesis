---
name: plan-reviewer
description: >
  Get a second model's verdict on a drafted Epic or story plan before any work is
  dispatched: run the deterministic plan check, then plan_review.py, and send needs-work
  findings back to the author for at most 3 rounds. Trigger phrases: "review this
  plan", "second opinion on the epic", "is this story ready to dispatch", "check the
  plan with another model", "plan review". Use after epic-composer or story-decomposer
  drafts a plan and before wave-dispatcher runs it.
---

# Plan Reviewer

<!--
  The skill itself. OpenCode reads it here; Claude Code loads it through the
  generated .claude/skills/<name>/SKILL.md pointer.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 1.0.0, owner: John D
  invokes: .agents/scripts/plan.py,
           .agents/scripts/plan_review.py
  doctrine: .agents/doctrine/escalation.md,
            .agents/doctrine/agent-plan-schema.md
-->

Gate a drafted plan before dispatch. `plan.py check` catches what a script can
(schema, ownership, waves); `plan_review.py` asks a different model, through
`opencode run`, whether the plan is ready against the epic and story rubrics.
You run both, route the verdict, and never review the plan yourself in place of
the second model: the point is a reader that did not write it.

## Inputs

- Required: one or more plan files (Epic or story bodies with an `agent-plan`
  block), or the issue references to save them from.
- Optional: `--model M` (default `$PLAN_REVIEW_MODEL`, else
  `nvidia/nvidia/nemotron-3-ultra-550b-a55b`), `--timeout` seconds.
- Read: the output of `plan.py check`, the JSON `plan_review.py` prints, and
  `.agents/doctrine/escalation.md` when a loop runs out.
- Do not read: the rubrics or the codebase to second-guess the reviewer.

## Deterministic Steps

Run from the repository root; `r=".agents/scripts/plan_review.py"`.

1. **Check.** `python3 .agents/scripts/plan.py check <plan-file>...`. Exit
   non-zero → return its findings to the author and stop; a plan that fails
   the check is not sent for review.
2. **Review.** `python3 $r <plan-file>... [--model M]`. It prints JSON
   `{"verdict", "findings", "model"}`. Key on the **exit code**, not on prose:
   - `0` ready → report ready with the model name; the plan may go to
     wave-dispatcher.
   - `1` needs-work → send every finding, verbatim, back to the author
     (epic-composer or story-decomposer, or the human who wrote it). After the
     author revises, go back to step 1. This is one round.
   - `2` blocked → report the findings as questions for a person; stop.
   - `3` couldn't review (the JSON says `"verdict": "unreviewed"` and gives
     an `error`: health check failed, timeout, unparseable answer) → this is
     **never** ready. Escalate per `.agents/doctrine/escalation.md`
     (`needs-input`): report the error and the model and ask a person whether
     to retry later, pick another `--model`, or review by hand.
3. **Bound the loop.** At most 3 needs-work rounds. If the third revision
   still comes back `1`, stop revising: write the diagnosis the escalation
   ladder asks for (the findings from each round, what changed between them,
   the cause marked confirmed or suspected) and take one rung — a replan or a
   person. Never start a fourth round with the same information.

## LLM Judgment

Use judgment only for:

- whether a revision actually addresses each finding before re-running, so a
  round is not spent on an unchanged plan;
- the cause and rung in the diagnosis after the third round.

Do not soften, drop or merge the reviewer's findings, do not overrule its
verdict, and do not pass `--auto` or let the reviewer edit anything.

## Output

```markdown
Plan review: <files>    Model: <model>    Round: <n>/3

Check: pass | fail (<n> findings)
Verdict: ready | needs-work | blocked | unreviewed (exit <code>)

Findings:
1. <verbatim finding>

Next: dispatch | back to <author> | person decides: <question> | escalated: <rung>
```

## Stop Conditions

- Stop if `plan.py check` fails; the author fixes it first.
- Stop on exit 2 (blocked) or exit 3 (couldn't review); never report either as
  ready.
- Stop after 3 needs-work rounds and escalate.
- Do not edit the plan yourself unless you are also its author in this session.

## Token Budget

- Default: the check output and the review JSON; read a plan file only to
  confirm a revision addressed a finding.
- Keep each round's report to the block above, ≤ 250 words plus the findings.
