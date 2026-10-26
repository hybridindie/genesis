---
read_when: "Adding or changing a CLI command, flags, output, or exit behaviour"
---

# CLI: Predictable Exit Codes, Machine-Readable Output

## MUST

- Exit `0` success, `1` expected failure, `2` usage error. Nothing else without
  documenting it.
- Data to stdout; logs, progress, and errors to stderr.
- `--json` emits one machine-parseable document; no ANSI, no banners, no
  prompts.
- Non-interactive by default: never prompt in a pipe or CI. Destructive
  commands require an explicit flag (`--yes` / `--force`).
- `--dry-run` prints the planned effect and changes nothing.
- Commands are idempotent where the operation allows it; re-running is safe.
- Config precedence is documented: flag > env > project file > user file > default.
- Handle SIGINT by cleaning up and exiting non-zero; no half-written state.

## SHOULD

- `--help` shows examples, not just flag names.
- `--version` prints one line.
- Human output is stable enough to read, never parsed by your own code.
- Errors name the failing input and the next action.

## ANTI-PATTERNS

- Interactive confirmation inside a pipeline.
- Writing data and logs to the same stream.
- Exit `0` after a partial failure.
- Silently ignoring an unknown flag.
- Colour codes when stdout is not a TTY.

## Checklist

- [ ] Exit codes documented.
- [ ] stdout/stderr separated.
- [ ] `--json` and `--dry-run` behave.
- [ ] Works non-interactively.
