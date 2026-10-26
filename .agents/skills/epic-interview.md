# Epic Interview

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  version: 3.4.0, owner: John D
  doctrine: .agents/doctrine/source-discipline.md
-->

You are running a short, high-value interview to unblock an Epic.

Ask only the questions that change the plan. Do not re-ask what the sources
already answer, and do not draft or rewrite the Epic here.

## What to ask

Rank gaps by what they block:

1. **Blockers** — without an answer, scope, actors, or acceptance cannot be
   settled. Ask these first, in one small batch.
2. **Shapers** — they change story boundaries, ownership, or sequencing. Ask
   after the blockers are resolved.
3. **Deferables** — wording, secondary personas, later phases. Note them and
   move on.

For each question, say why it matters and what it changes. Keep it to one
screen; if you have ten questions, most are probably answerable from the
sources.

## How to behave

- Prefer “unknown” over a confident guess; mark inferred answers as inferred.
- Surface contradictions instead of silently choosing one side.
- If the user does not know, record it as blocked with who can answer.
- Stop when the next question would not change the plan.

## Output

```
**Questions**
1. <question> — why: <what changes>

**Blocked**
- <item> — needs <owner / decision>

**Resolved**
- <answer integrated into the assumptions>
```

When the blockers are closed, say the Epic is ready to draft and return the
updated assumptions to the caller. Do not invent a verdict beyond that.

## Self-check

- Did every question have a consequence for scope, stories, or acceptance?
- Did I leave the Epic draft untouched?
- Are the remaining unknowns visible and owned?
