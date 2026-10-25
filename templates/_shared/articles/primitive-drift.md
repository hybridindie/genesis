---
description: "Use when editing rule files in .claude/rules/ or instruction files in .github/instructions/ — warns when the corresponding mirror file has drifted and needs updating."
paths:
  - ".claude/rules/**"
  - ".github/instructions/**"
---

# Primitive Drift: Rule/Instruction Mirror Sync

`.claude/rules/` (Claude Code) and `.github/instructions/` (GitHub Copilot) are mirrors of the same rules. They intentionally have different frontmatter — Claude uses `paths:`, Copilot uses `applyTo:` — but the **body content must be identical**.

## Mirror Pairs (Single Source of Truth)

The canonical mirror pair list lives in the project root at `templates/_shared/mirror-pairs.json`.
**Do not edit the table below manually** — if you need to add or remove an article, update the JSON and re-run the bootstrap script.

To see the current mirror pairs, read `templates/_shared/mirror-pairs.json`.

## When You Edit One File

Always update the mirror in the same edit. The body content (everything after the frontmatter `---` block) must stay identical between the two files. Do not change the frontmatter of the mirror — only update the body.

If you detect that the bodies have drifted, warn the user:

> **PRIMITIVE-DRIFT**: `<file>` and its mirror `<mirror>` have diverged. Update both to match before proceeding.

To verify sync manually:

```bash
bash .claude/hooks/check-primitive-drift.sh
```

## How `check-primitive-drift.sh` Works

1. Reads `templates/_shared/mirror-pairs.json` for the canonical pair list.
2. For each pair, extracts the body (after second `---` frontmatter delimiter).
3. Compares the two bodies byte-for-byte.
4. Reports any drift with the exact file paths.

## Adding a New Constitutional Article

1. Add a new entry to `templates/_shared/mirror-pairs.json`:
   ```json
   {
     "article": "X",
     "title": "New Article Title",
     "claude_file": "backend/new-article.md",
     "copilot_file": "backend-new-article.instructions.md",
     "render_dir": ".claude/rules/backend",
     "copilot_description": "New Article Title (Article X)",
     "paths": ["{{BACKEND_PATH}}/src/libs/**/*.py"]
   }
   ```
2. Create the shared source file at `templates/_shared/articles/backend/new-article.md` (or the appropriate subdirectory).
3. Re-render into the target project: `bash templates/scripts/bootstrap.sh ...`
4. Verify: `bash .claude/hooks/check-primitive-drift.sh`

**Never** add a new `.claude/rules/` file without adding it to `mirror-pairs.json` — the mirror will not be generated, and the article will be invisible to GitHub Copilot.
