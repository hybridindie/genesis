# Source Structure

On-demand section — read when editing the genesis repo structure.

Two products: the **project harness** (`templates/`) and the **system layer**
(`system/`), which configures a machine.

```
system/                       ← machine layer (SYSTEM.md, system/README.md)
  install.sh                  ← renders into $HOME (idempotent, --diff/--force)
  shell/ agents/ git/ herdr/ zed/ bin/ Brewfile

new-project.sh                ← create a repo + render the harness
scripts/lint-skills.py        ← enforce the deterministic skill contract
.agents/scripts/validate_artifact.py ← validate Epic/story/task/AC shapes

templates/
  _shared/
    AGENTS.md                 ← canonical project context (stack blocks, generated lists)
    my-workflows.md           ← personal cross-project conventions
    core/articles/            ← rules for every project
    agents/ commands/ skills/ ← shared by every project
    doctrine/                 ← skill-execution contract (rendered to rules/doctrine/)
    stacks/<id>/              ← python mcp agent fastapi frontend godot godot-addon rust
                                 each: articles/ agents/ commands/ skills/
    packs/<id>/               ← production, acd (opt-in)
    ci/base.yml, ci/jobs/     ← CI composed from one job per stack
    githooks/                 ← tracked pre-commit / pre-push gates
    mirror-pairs.json         ← doctrine routing
  claude-code/                ← Claude assets (hooks, thin CLAUDE.md)
  opencode/                   ← OpenCode config (instructions, v2 permissions)
  scripts/
    bootstrap.sh              ← wrapper for render.py
    render.py                 ← renderer: stacks + packs, conditionals, manifest, CI
    inspect-project.py        ← stack/path/tooling detection (read-only)
    generate-rule-index.py    ← rule index + command/skill lists in AGENTS.md
    generate-harness-mirrors.py ← mirrors every Claude agent/command into .opencode/
    check-harness-sync.py, validate-render.py ← checks
    scaffold.py               ← optional README/LICENSE/Makefile/Python skeleton
```

### How rendering works

1. Resolve stacks (manifest, flags, detection) and add implied ones.
2. Render core, then each stack, then each pack: `articles/` into
   `.claude/rules/`, plus `agents/`, `commands/` and `skills/`. Article paths
   must be unique; a collision is an error, not an override.
3. Each file is rendered in memory: `{{#FLAG}}…{{/FLAG}}` blocks
   (`STACK_*`, `PACK_*`, tooling flags), then `{{PLACEHOLDER}}` values.
4. Compose CI, write `.claude/harness.json`, mirror agents/commands to
   `.opencode/`, and generate the rule index and command/skill lists.

Adding a rule: put it under `core/articles/` (every project),
`stacks/<id>/articles/` or `packs/<id>/articles/`, give it `read_when:`
frontmatter, and re-render.

Editing this repo (versioning, drift policy, hooks)? See
[`CONTRIBUTING-HARNESS.md`](../../CONTRIBUTING-HARNESS.md).
