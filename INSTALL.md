# Install the harness into your project

Fetch this repo and tailor a complete AI harness (Claude Code + Opencode +
GitHub Copilot) into any project. The repo is public, so nothing here needs
authentication. All routes run the same flow defined in
[`.agents/skills/bootstrap-harness.md`](.agents/skills/bootstrap-harness.md).

---

## Easiest — one command

From inside the project you want to tailor:

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/genesis/main/install.sh | bash
```

That clones the genesis repo into `~/.cache/genesis` and renders a
harness tailored to the current directory via auto-detection. No interview, no auth.

Options (pass after `bash -s --`):

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/genesis/main/install.sh \
  | bash -s -- --output-dir /path/to/project --ref main
```

## Interactive — single prompt (Claude Code or Opencode)

When you want a plan review and to be asked about things auto-detect can't infer
(domain, compliance, coverage tiers), paste this to your agent from the project:

```
Fetch the AI harness genesis repo and tailor a complete harness into THIS project.

1. Clone or update it:
   git clone --depth 1 https://github.com/hybridindie/genesis.git ~/.cache/genesis 2>/dev/null \
     || git -C ~/.cache/genesis pull --ff-only

2. Read and follow ~/.cache/genesis/.agents/skills/bootstrap-harness.md,
   using the current directory as the target output-dir.

Probe my stack, show me the install plan, ask only about genuine unknowns,
then render, validate, and report.
```

Works identically in Claude Code and Opencode.

## From a clone of this repo

If you already have the genesis repo open:

- **Claude Code / Opencode:** run `/bootstrap-harness` (pass an output dir as the
  argument, or run it from the target project).
- **Claude Code / Copilot agent:** `@install-harness /absolute/path/to/target`.

---

**Requirements:** `git` and `python3`. No GitHub auth needed — the repo is public.
