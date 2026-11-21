---
read_when: "Adding or changing a CLI command, flags, output, or exit behaviour"
paths:
  - "**/cli.py"
  - "**/cli/**/*.py"
  - "**/__main__.py"
  - "**/commands/**/*.py"
---

# CLI: Predictable Exit Codes, Machine-Readable Output

## MUST

- Exit `0` success, `1` expected failure, `2` usage error. Nothing else without
  documenting it.
- Data to stdout; logs, progress, and errors to stderr.
- Commands whose output another program reads offer `--json`: one
  parseable document, no ANSI, no banners, no prompts.
- Non-interactive by default: never prompt in a pipe or CI. The confirmation
  and preview `security.md` requires are `--yes` and `--dry-run`.
- Commands are idempotent where the operation allows it; re-running is safe.
- Config precedence is documented: flag > env > project file > user file > default.
- Handle SIGINT by cleaning up and exiting non-zero; no half-written state.

## SHOULD

- `--help` shows examples, not just flag names.
- `--version` prints one line.
- Human output is stable enough to read, never parsed by your own code.

## ANTI-PATTERNS

- Interactive confirmation inside a pipeline.
- Writing data and logs to the same stream.
- Silently ignoring an unknown flag.
- Colour codes when stdout is not a TTY.
