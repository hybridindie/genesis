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

templates/
  _shared/
    AGENTS.md                 ← canonical project context (rule-index marker)
    my-workflows.md           ← cross-project conventions (loaded by OpenCode)
    core/
      articles/               ← rules shipped for every profile
    agents/                   ← shared agents (article-compliance-reviewer)
    commands/                 ← shared commands (preflight, graphify, sessions)
    doctrine/                 ← referenced rules (rendered to rules/doctrine/;
                                 includes skill-execution.md)
    skills/                   ← shared skills (customize-harness, gen-contract-test, …)
    ci/                       ← per-profile CI workflow templates
    githooks/                 ← tracked pre-commit / pre-push gates
    profiles/
      mcp/                    ← articles/ commands/ agents/ skills/
      python/
      agent/
      web/                    ← includes the operational SaaS articles
      godot/
    mirror-pairs.json         ← routing for agent/command/doctrine mirrors
  claude-code/                ← Claude assets (hooks, thin CLAUDE.md)
  opencode/                   ← OpenCode config (instructions, v2 permissions)
  scripts/
    bootstrap.sh              ← main renderer (profile selection + detection)
    generate-rule-index.py    ← builds the AGENTS.md rule index from read_when
    generate-harness-mirrors.py ← mirrors Claude agents/commands into .opencode/
    inspect-project.py        ← stack/version detection (feeds --auto-detect)
    process-conditionals.py   ← strips {{#FLAG}} blocks (profile + feature)
    scaffold.py               ← optional README/LICENSE/Makefile/Python skeleton
```

### How article rendering works

1. Render `_shared/core/articles/**` into `.claude/rules/**`, preserving paths.
2. Render `_shared/profiles/<profile>/articles/**` into the same tree — a file
   with the same relative path **overrides** the core article.
3. `generate-rule-index.py` scans the rendered rules, reads each `read_when:`,
   and replaces `<!-- RULE_INDEX -->` in `AGENTS.md`.
4. `process-conditionals.py` strips profile/feature blocks from every file.

Adding a rule: put it under `core/articles/` (all profiles) or
`profiles/<profile>/articles/` (one profile), give it `read_when:` frontmatter,
re-render, and the index updates itself.

Editing this repo (versioning, drift policy, hooks)? See
[`CONTRIBUTING-HARNESS.md`](../../CONTRIBUTING-HARNESS.md).
