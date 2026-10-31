# Bootstrap / Install Harness

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 6.0.0, owner: John D
  invokes: templates/scripts/render.py (via bootstrap.sh),
           templates/scripts/validate-render.py
-->

Install, update, or extend the genesis harness in a target project. A project
gets the core rules plus every stack it uses (`python`, `mcp`, `agent`,
`fastapi`, `frontend`, `godot`, `godot-addon`, `rust`) and any opt-in packs
(`production`, `acd`). The renderer detects stacks; the model only confirms the
plan with the user and runs the semantic passes.

## Inputs

- Required: the target project directory (default: current directory).
- Optional: stack/pack changes from the user ("add rust", "drop frontend",
  "with the production pack").
- Read: nothing up front. Read a manifest only if the plan shows a stack the
  user disputes.
- Do not read: source trees, generated harness output, or unrelated repos.

## Deterministic Steps

1. **Resolve genesis.**

   ```bash
   if [[ -f templates/scripts/render.py ]]; then
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
   TARGET="$(cd "${1:-$PWD}" && pwd)"
   ```

2. **Plan.** Build the flags from the user's request (`--add-stacks`,
   `--remove-stacks`, `--stacks`, `--packs`) and print the plan without
   writing:

   ```bash
   python3 "$GENESIS/templates/scripts/render.py" --output-dir "$TARGET" --auto-detect --plan <flags>
   ```

   On an installed harness (`.claude/harness.json` exists) the recorded stacks
   and packs are the starting point; detection only fills gaps.

3. **Confirm.** Show the plan table below and ask: "Proceed? Reply yes, or
   name stacks/packs to add or drop." On an update, list `kept_local_edits`:
   files edited since the last render are kept, not overwritten (as are
   `my-workflows.md`, existing `.githooks/` and existing CI). New stack rules
   are still added and indexed. Re-run step 2 if the user changes anything.

4. **Render.**

   ```bash
   bash "$GENESIS/templates/scripts/bootstrap.sh" --output-dir "$TARGET" --auto-detect <confirmed flags>
   ```

5. **Validate.**

   ```bash
   python3 "$GENESIS/templates/scripts/validate-render.py" --genesis "$GENESIS" --target "$TARGET"
   ```

6. **Semantic pass (fresh installs, interactive only).** Run `/harness-eval`,
   then `/customize-harness`, each with its own plan and confirmation.

## LLM Judgment

- Whether a detected stack is real when the evidence is thin (e.g. an LLM SDK
  plus an `evals/` dir suggests `agent`). Ask rather than guess.
- Whether to offer the `production` pack (`packs_suggested`) and, only if the
  user asks for strict agent sessions, the `acd` pack.

Paths, versions, package managers and commands come from the renderer; don't
override them by inspection.

## Output

Plan:

```markdown
| | Value |
|---|---|
| Target | <path> (fresh install / update) |
| Stacks | <list>  — evidence: <one line each> |
| Packs | <list or none>  (suggested: <list>) |
| Paths | python=<…> frontend=<…> godot=<…> rust=<…> |
| Files | <count> |
```

Result:

```markdown
Harness <installed|updated> in <path>: stacks <list>, packs <list>.
Validation: PASS | FAIL <first errors>
Next: <up to three actions>
```

## Stop Conditions

- Genesis can't be fetched, the target is missing, or the render fails.
- Validation fails: report the errors; don't patch the output by hand.
- The user hasn't confirmed the plan.
- Never edit `$GENESIS/templates/` during an install.

## Token Budget

- One plan run, one render, one validation; no repository tour.
- Plan and report ≤ 250 words each.
