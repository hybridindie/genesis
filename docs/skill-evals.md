# Skill Evals

Two tiers, deliberately different in cost and in when they run.

## Deterministic — every push

No model calls. `tests/test_evals.py` validates the golden artifacts in
`tests/evals/` against `.agents/scripts/validate_artifact.py` and checks the
invariants the rubrics describe:

- every story row cites an AC declared in the epic, and every AC is realised by
  a story;
- waves never own the same file;
- a story says what it owns and what it does not.

It also pins the validators themselves (`tests/test_validate_artifact.py`), so a
parser change is a deliberate decision. This runs in the `unit` job on every
push because it is fast, hermetic, and catches contract drift early.

## Behavioural — only when a skill body changes

These need a model, so they are never scheduled. They run when the detector says
a skill changed:

```bash
python3 scripts/changed-skills.py --base origin/main
# story-decomposer: 1 behavioural case(s)
#   - tests/evals/behaviour/story-decomposer/thin-epic.md
```

A "skill change" is a body under `.agents/skills/<name>.md`, a
`templates/_shared/**/skills/<name>/SKILL.md`, or that skill's `scripts/`.
Generated wrappers (`.claude/`, `.opencode/`) and docs do not count.

For each reported skill, run its cases in a subagent or a fresh session: feed
the case's **Input** to the skill, then check the produced artifact against the
case's **Expected properties**. Record the outcome in the PR that changed the
skill, with the model and the case name. There is no pass/fail threshold to
game — a case either produced the properties or did not.

CI prints the same report on PRs (the `skill-evals` job) so a skill change
without a case is visible in review. It does not call a model and does not gate
the merge; the judgement is yours.

### Adding a case

```
tests/evals/behaviour/<skill>/<case>.md
```

```markdown
# Case: <what makes this input interesting>

## Input

<the material the skill receives — a transcript, a thin epic, a contradiction>

## Expected properties

- <a property of the output, checkable without reading prose style>
- <what the skill must refuse or escalate instead>
```

Keep cases adversarial: thin input, contradictory input, input that pulls the
skill outside its scope. A case that restates the happy path tests nothing.

**Every skill must have at least one case** — `tests/test_eval_coverage.py`
enumerates the skills from `.agents/skills/` and
`templates/_shared/**/skills/` and fails when one has none, so coverage cannot
regress as skills are added.
