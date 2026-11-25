# Skill Evals

Three tiers, deliberately different in cost and in when they run.

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
without a case is visible in review. For behavioural cases it does not call a
model and does not gate the merge; the judgement is yours. Fixture cases are
different: see below.

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

## Fixture evals — scored, tracked, gated

`.agents/evals/cases/<case>/` holds full-workspace cases for the epic pipeline
skills: a scaffolded repo (`_fixture/reports-app`), a realistic prompt, and
graders. `claude plugin eval` runs each case several times and scores it 0..1;
`scripts/eval-gate.py` turns that into a regression gate.

```bash
python3 scripts/eval-gate.py --base origin/main          # cases for changed skills
python3 scripts/eval-gate.py --skill epic-composer --runs 5
python3 scripts/eval-gate.py --all --runs 5 --update-baseline
mlflow ui --backend-store-uri sqlite:///mlflow.db        # compare runs
```

- **Selection.** Each case's `prompt.md` carries a `skill:<name>` tag; a changed
  skill runs its tagged cases. A skill with only behavioural cases is reported.
- **Gate.** A case fails when its score falls more than `--tolerance` (0.15)
  below `.agents/evals/baseline.json`. Errored runs score 0, so an outage is a
  failure, not a pass. A partial result (cost ceiling, auth) is never gated on.
  A case with no baseline is reported; `--strict` fails it.
- **Baseline.** Only `--update-baseline` writes it, from a real run. Change it
  in the same PR as the skill change that justifies it, so review sees both.
- **Tracking.** With `mlflow` installed every invocation is one MLflow run in the
  `genesis-skill-evals` experiment: git sha, models, per-case score and delta,
  cost, duration, the gate verdict, and the raw `aggregate-result.json`.
- **CI.** The `skill-evals` job runs the gate on PRs when the repository has an
  `ANTHROPIC_API_KEY` secret, capped at $10 a run, and uploads the record.

### Grader rules

- **A fact a script can settle is not judged.** File counts, "exactly one
  agent-plan block", "`plan.py validate` printed PASS", "no branch was created"
  are `regex`, `file_exists` or `tool_used` graders: free, and the same answer
  every time. `tests/test_eval_gate.py` fails when one of those phrases sits in
  an `llm` grader.
- **Point the judge at the evidence.** An `llm` grader on `focus: trace` sees
  only the first and last 12 messages of a 40-turn run, which is rarely where
  the file was written. Judge the output file (`focus: { source: file, path:
  epic.md }`) or the final answer (`last_message`). Graders that span several
  output files stay on the trace; treat them as the weakest signal.
- **Check the skill fired.** Every case has a `00-skill-fired` `tool_used: Skill`
  grader with `arm: with-only`: an indicator, not scored, that separates "the
  skill got worse" from "the skill never triggered".
- `tests/test_eval_gate.py` lints every grader's frontmatter against the
  documented schema, so a typo fails on push rather than after a paid run.
