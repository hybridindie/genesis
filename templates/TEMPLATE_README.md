# Template System

How `templates/` produces a project harness. The file tree and rendering steps
are in [`docs/agents-sections/source-structure.md`](../docs/agents-sections/source-structure.md);
the stack and pack catalogue is in the top-level [`README.md`](../README.md#stacks-and-packs).

## In one paragraph

`scripts/render.py` (wrapped by `scripts/bootstrap.sh`) takes the core rules,
the project's stacks (`_shared/stacks/<id>/`) and its opt-in packs
(`_shared/packs/<id>/`). It renders each file in memory: first the
`{{#FLAG}}` blocks, then the `{{PLACEHOLDER}}` values. The output goes into
`.claude/` and `.opencode/`, and `.claude/harness.json` records what was
rendered. The project drift gate holds the tree to that manifest.

## Checks

```bash
for s in python mcp agent fastapi,frontend godot,rust mcp,godot-addon; do
  out="/tmp/render-${s//,/-}"; rm -rf "$out"
  python3 templates/scripts/render.py --output-dir "$out" --project-name Test --stacks "$s" --packs production,acd
  python3 templates/scripts/check-harness-sync.py templates "$out"
  python3 "$out/.claude/hooks/check-project-drift.py" --root "$out"
done
```

CI (`.github/workflows/validate-templates.yml`) runs this matrix. It also checks
for unresolved placeholders and conditionals, valid rendered JSON/YAML,
identical OpenCode mirrors, and that a rule from an undeclared stack fails the
drift gate.
