# My Workflows

> Personal, cross-project conventions. `customize-harness` reads this file and
> weaves the relevant parts into the project's `CLAUDE.md` / `AGENTS.md` / rules
> during install and on every re-run. Fill in what matters; delete the rest.
> **Sections left as placeholders are skipped**, so an unfilled file is harmless.
>
> This is your boilerplate default: edit it in the genesis repo and every future
> install inherits it. Each installed project also gets its own editable copy.

## Version control

- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`), imperative
  subject ≤ 72 chars; the body explains why, not what.
- Trunk-based: short-lived branches off `main`, squash-merge, delete the branch.
- Every PR references its issue (`closes #N`) and lists a Test plan.
- `push.autoSetupRemote` is on; force-push only with `--force-with-lease`.
- Read the full diff before committing. Never commit generated output, `.env`
  files, or anything with credentials.

## Testing

- TDD: write the failing test first; every bug fix ships with a regression test.
- Zero unchecked skips/xfail. Determinism is mandatory: inject clocks and fakes —
  no `sleep`, real sockets, wall-clock or RNG dependence.
- Coverage floors: safety/critical paths 90%, core logic 70%, helpers 50%.
- Treat "suite green" as a binary signal: a half-passing suite is a broken signal,
  not partial success.

## Code review

- Review the diff, not the summary. Reject `ok: true` on a half-finished operation.
- Errors are structured data with an actionable hint; no raw stack traces cross a
  module or protocol boundary.
- No machine-specific paths, secrets, or `.env` contents in code, logs, or commits.
- Every review comment gets either a code change or a written reply.

## Preferred tooling & commands

### Shell and scripts

- Non-interactive shells (`zsh -c`, `bash -c`, CI, MCP servers) are silent, have
  the full PATH, and load **no aliases**. Scripts call real binaries (`ls`, `jq`),
  never interactive aliases (`ll`, `k`, `lt`).
- `$EDITOR` / `$VISUAL` must block until the file is closed (e.g. `zed --wait`).
  A GUI editor that returns immediately breaks `git commit` and every tool that
  shells out to an editor.
- Keep shell init free of output; printing from `.zshenv` / `.zshrc` corrupts
  output captured by agents and scripts.

### Search and inspection

- Content search: `rg`. Path search: `fd` (or `rg --files`). YAML: `yq`.
- Human-facing renderers (`eza`, `bat`, `delta`, colourised `ls -l`) are for
  reading only. Use `ls -1`, `cat`, `rg --json`, `jq`, `git --no-pager diff` for
  anything that is parsed.

### Project environment

- direnv owns per-project environment: commit `.envrc` (no secrets), keep `.env`
  gitignored, and commit `.envrc.example` documenting required variables.
- Non-interactive runs use `direnv exec . <cmd>`; never `direnv allow` a file you
  have not read.
- Never assume a daemon (Docker, database, cache) is running unless the project's
  README says how to start it.

### Agent permissions

- Default **allow** for routine commands; **ask** before `sudo`, `rm -rf`, package
  installs/upgrades, `git push --force`, and `direnv allow`.
- **Deny** reads of credential paths: `~/.ssh`, `~/.aws`, `~/.kube`, `**/.env`,
  and provider secret files.
- OpenCode (v2) uses an ordered `permissions` array where the **last** matching
  rule wins; Claude Code uses `deny → ask → allow` where the **first** match wins.
  Do not copy rules between them without reordering.
- Permissions reduce accidents; they are not a sandbox (shell patterns are prefix
  matches, not an interpreter).

## House style

- Comments explain *why*. Naming: `snake_case` for data/domain fields,
  `cmd_<verb>_<noun>` for command handlers.
- Report honest partial results (aborted steps, skipped inputs, non-atomic batches)
  instead of a blanket success.
- Configuration is code: version it, keep secrets out, and record one-off machine
  fixes in the repo README.
