# Source Structure

On-demand section — read when editing the genesis repo structure.

Two products live here: the **project harness** (`templates/`) and the **system
layer** (`system/`), which configures a machine.

```
system/                 ← machine layer (see SYSTEM.md and system/README.md)
  install.sh            ← renders into $HOME (idempotent, --diff/--force)
  shell/                ← zsh config -> ~/.config/zsh + $HOME loaders
  agents/               ← user-level AGENTS.md, CLAUDE.md import, global configs
  git/                  ← shared gitconfig + global gitignore
  herdr/ zed/ bin/      ← optional tool configs and wrappers
  Brewfile              ← macOS/Linuxbrew package set
new-project.sh          ← create a repo + render the harness in one step

templates/
  _shared/
    articles/      ← Constitutional rules (rendered into all three harnesses)
    agents/        ← Shared agent definitions (Claude frontmatter → Copilot transformed)
    commands/      ← Shared commands/prompts (body identical across platforms)
    doctrine/      ← Shared rules referenced by multiple articles/agents (rendered to .claude/rules/doctrine/)
    skills/        ← Shared shippable skills (rendered into target .claude/ + .opencode/)
    my-workflows.md ← Your cross-project conventions; shipped into each project and
                      applied by the customize-harness skill (edit once, all installs inherit)
    database/      ← SQL and infrastructure rules
    frontend/      ← Frontend conventions
    mirror-pairs.json  ← Single source of truth for all mirror pairs (entries, agent_entries, command_entries, doctrine_entries)
  claude-code/    ← Claude-specific harness assets (skills, hooks, scripts)
  github-copilot/ ← Copilot-specific assets (prompts that aren't mirrored commands)
  opencode/       ← Opencode-specific assets
  scripts/
    bootstrap.sh                 ← Main installer
    generate-copilot-mirrors.py  ← Transforms Claude frontmatter → Copilot frontmatter (skips doctrine/)
    inspect-project.py           ← Detects project stack (used by --auto-detect)
    process-conditionals.py      ← Strips {{#FLAG}}...{{/FLAG}} blocks
```

Editing this repo (adding articles/agents/commands/doctrine, versioning,
drift policy, hook behavior)? See [`CONTRIBUTING-HARNESS.md`](../../CONTRIBUTING-HARNESS.md).