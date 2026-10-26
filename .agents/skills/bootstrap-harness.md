# Bootstrap / Install Harness

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 5.0.0, owner: John D
  invokes: templates/scripts/inspect-project.py,
           templates/scripts/bootstrap.sh,
           templates/scripts/check-harness-sync.py
  doctrine: templates/_shared/doctrine/skill-execution.md
-->

Fetch the genesis repo if needed, inspect the target deterministically, render
one profile, validate the result, then optionally run the semantic evaluation
and customization steps. The model is used for the interview and for semantic
review, not for file discovery.

## Inputs

- Required: the target project directory (default: current directory).
- Optional: profile/flag overrides, `--merge` is not accepted here.
- Read after inspection: `README.md`, `pyproject.toml`, `package.json`, and
  `project.godot` only when the inspector leaves a required field empty.
- Do not read: every source file, generated harness output, or unrelated repos.

## Deterministic Steps

1. **Resolve genesis.** Run this from the target or any directory:

   ```bash
   if [[ -f templates/scripts/bootstrap.sh ]]; then
     GENESIS="$PWD"
   else
     CACHE="${GENESIS_CACHE:-$HOME/.cache/genesis}"
     REF="${GENESIS_REF:-main}"
     if [[ -d "$CACHE/.git" ]]; then
       git -C "$CACHE" pull --ff-only --quiet origin "$REF"
     else
       git clone --quiet --depth 1 --branch "$REF" \
         https://github.com/hybridindie/genesis.git "$CACHE"
     fi
     GENESIS="$CACHE"
   fi
   test -f "$GENESIS/templates/scripts/bootstrap.sh"
   ```

   If the clone fails, stop and report the git/network error.

2. **Resolve the target.** `TARGET="$(cd "${1:-$PWD}" && pwd)"`; stop if it does
   not exist.

3. **Classify fresh vs update.** If `$TARGET/.claude/rules` exists, use the
   update path below. Otherwise continue.

4. **Inspect once.** Run the deterministic inspector and keep its JSON:

   ```bash
   python3 "$GENESIS/templates/scripts/inspect-project.py" "$TARGET"
   ```

   Use `profile`, `project_name`, `project_slug`, versions, and `confidence` from
   that result. Do not run manual probes or list the repository.

5. **Plan review.** Show the fixed plan table: profile, detected stack, files to
   install, omitted profiles, and any missing required field. Ask only for gaps
   that would change the profile or a required flag; at most three questions.
   Ask “Proceed with this plan? Reply yes, or describe changes.”

6. **Render.** Run exactly:

   ```bash
   bash "$GENESIS/templates/scripts/bootstrap.sh" \
     --auto-detect --output-dir "$TARGET" <confirmed flags>
   ```

   Capture stdout; stop on a non-zero exit.

7. **Validate.** Run the single deterministic validator and report only failures:

   ```bash
   python3 "$GENESIS/templates/scripts/validate-render.py" \
     --genesis "$GENESIS" --target "$TARGET"
   ```

   It owns the required files, project drift, harness sync, and hook syntax
   checks. If it fails, stop; do not paper over it.

8. **Semantic pass (interactive only).** Run the shipped `/harness-eval`, then
   `/customize-harness` against `$TARGET`, showing each plan and getting
   confirmation before edits. Skip this phase when the caller asked for a
   non-interactive install.

9. **Report.** State the installed profile, created file counts, validation
   state, and the next three actions.

## LLM Judgment

Use judgment only for:

- the domain/compliance questions the inspector cannot answer;
- reviewing the rendered rules for stack fit (`/harness-eval`);
- weaving the user's conventions from `my-workflows.md` into `AGENTS.md`
  (`/customize-harness`).

Do not choose paths, versions, package managers, or commands by inspection; the
inspector and bootstrap own those.

## Output

```markdown
Harness installed in: <TARGET>
Profile: <profile>    Confidence: <inspector confidence>

Created: <counts for rules, agents, commands, skills, mirrors>
Validation: PASS | FAIL <list>
Next:
1. <action>
2. <action>
3. <action>
```

For an update, use `Harness updated in: <TARGET>` and include a short diff
summary: files refreshed, files unchanged, and warning that generated files were
rewritten.

## Update Path

1. Show current counts with `find`/`ls`; do not read file bodies.
2. Re-run the inspector and show what will be refreshed, plus the warning that
   bootstrap owns generated files and overwrites local customizations.
3. Ask for confirmation, then render and validate exactly as steps 6–7.
4. Report as above; do not run `/customize-harness` unless requested.

## Stop Conditions

- Stop if genesis cannot be fetched, the target is missing, or bootstrap fails.
- Stop if `check-project-drift.py` or `check-harness-sync.py` fails.
- Stop if the inspector cannot choose a profile and the user does not answer the
  one profile question.
- Never edit `$GENESIS/templates/` during an install.

## Token Budget

- One inspector run; no manual probe list, no repository tour.
- Read at most five target files, and only when the inspector leaves a field
  empty.
- At most three interview questions; report ≤ 250 words.
- Reuse the plan/report templates; do not restate the skill.
