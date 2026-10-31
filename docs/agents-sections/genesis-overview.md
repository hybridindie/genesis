# What It Does / Install / Key Flags

On-demand section — read when installing or bootstrapping a harness.

`templates/scripts/render.py` (wrapped by `bootstrap.sh`) renders a project
harness from `templates/_shared/`: one canonical `AGENTS.md`, a thin
`CLAUDE.md`, the core rules, every detected stack's rules, and any opt-in
packs. The stack and pack tables are in the top-level
[`README.md`](../../README.md#stacks-and-packs).

> The **system layer** for the machine itself is `bash system/install.sh`; see
> [`SYSTEM.md`](../../SYSTEM.md).

| Platform | Entry point | Rules location |
|----------|-------------|----------------|
| OpenCode | `AGENTS.md` | `.claude/rules/` (read via the generated index) |
| Claude Code | `CLAUDE.md` (`@AGENTS.md`) | `.claude/rules/` (path-scoped) |

## Install

```bash
bash templates/scripts/bootstrap.sh --output-dir /path/to/project --auto-detect
python3 templates/scripts/render.py --output-dir /path/to/project --auto-detect --plan   # dry run
```

## Key flags

| Flag | Purpose |
|------|---------|
| `--output-dir` | Target project (required) |
| `--auto-detect` | Run `inspect-project.py` on the target (always on for a fresh install) |
| `--stacks a,b` | Set the stacks explicitly |
| `--add-stacks` / `--remove-stacks` | Adjust the stacks recorded in an installed `harness.json` |
| `--packs production,acd` | Opt-in packs (`--packs ""` clears them) |
| `--python-path`, `--frontend-path`, `--godot-path`, `--rust-path` | Override detected directories |
| `--project-name`, `--project-slug` | Names used in the context files |
| `--ci-platform github\|gitea\|none`, `--ci-runs-on LABEL` | CI target and runner |
| `--force-ci`, `--force-hooks`, `--force-workflows` | Replace an existing CI workflow, git hooks, or `my-workflows.md` |
| `--plan` | Print the resolved plan as JSON and write nothing |
| `--profile` | Legacy single profile (`web` → `fastapi,frontend`) |

On an installed harness, `harness.json` is the starting point and detection
only fills gaps. Old single-profile manifests (schema 1) are re-detected.
