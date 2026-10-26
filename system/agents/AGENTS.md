# Global rules — {{MACHINE_LABEL}}

Machine-level facts about the shell and tooling. Project-specific rules live in
each repo's `AGENTS.md` and win where they overlap. Rendered by
`system/install.sh` from the genesis repo — edit the source there, not this copy.

## Platforms

- macOS (Homebrew at `/opt/homebrew`) and Linux (Homebrew at
  `/home/linuxbrew/.linuxbrew`, or the distro package manager). Scripts should
  check `$OSTYPE` rather than assume one.
- Repositories live under `{{DEV_ROOT}}`.

## Shell

- zsh. Config lives in `~/.config/zsh/`; `$HOME/.{zshenv,zprofile,zshrc}` are
  one-line loaders. Machine values live in `conf.d/98-machine.zsh` (generated);
  personal tweaks belong in `conf.d/99-local.zsh` (user-owned).
- Non-interactive shells (`zsh -c`, `zsh -l -c`) are silent and already have the
  full PATH: Homebrew, `~/.local/bin`, `~/.opencode/bin`, pyenv shims,
  `~/.cargo/bin`. Don't hardcode absolute paths to those binaries.
- Non-interactive shells get **no** aliases, no zoxide `cd`, no direnv hook, no
  fzf/ZLE bindings and no prompt. Commands you run must use real binaries:
  `ls` (not the interactive `eza` alias), `jq` (not `jq -C`), no `lt`/`ll`/`k`.
- `$EDITOR`/`$VISUAL` must block until the file is closed (`zed-wait` on macOS,
  `nvim`/`vi` elsewhere). Never invoke a GUI editor directly from an agent and
  wait on it; it returns immediately.
- Keep `zsh -c` free of output. Startup files must never print.
- When telling the user how to accept an inline suggestion: `Tab` accepts one
  word, `Ctrl+Space` accepts the whole suggestion, and with no suggestion `Tab`
  opens the normal completion menu.

## Config version control

- System config (shell, agent rules, git defaults) is rendered from the genesis
  repo by `system/install.sh`; the rendered copies are what the machine runs, and
  the installer re-applies upstream changes. A private dotfiles repo may track
  machine state, but it must not symlink the same paths — one writer per path.
- Machine-specific values belong in `conf.d/98-machine.zsh` / `99-local.zsh`;
  never fork a numbered module for a local tweak.
- Never commit secrets: `.env` files, `~/.claude.json`, provider tokens, or
  anything under `~/.ssh`, `~/.aws`, `~/.kube`.

## Command choices

- Content search: `rg`, not `grep -r`.
- Path search: `fd` for name/extension queries; `rg --files` for a gitignore-aware
  file list. `fd` respects `.gitignore` by default.
- YAML: use `yq` to read or edit — don't hand-edit YAML with `sed`.
- Human-facing output is not for parsing: `eza`, `bat`, `delta` (the git pager) and
  colourised `ls -l` are for reading. Use `ls -1`, `cat`, `rg --json`, `jq`,
  `git --no-pager diff` when you consume output.
- Python: prefer `uv` for project environments; pyenv selects the global
  interpreter. Don't `pip install` into a pyenv global env without asking.
- Package installs: `brew` on macOS/Linuxbrew, `apt`/`dnf`/`pacman` on servers.
  Ask before installing, upgrading, or removing anything.

## Project environment

- direnv owns per-project env via `.envrc`. It auto-loads **only in interactive
  shells**; for `zsh -c` use `direnv exec . <cmd>` when a command needs that env.
- Never run `direnv allow` on an `.envrc` you haven't read; ask first.
- Don't assume a daemon (Docker, database, cache) is running unless the project's
  README says how to start it.

## Terminal (Herdr)

- If `HERDR_ENV=1`, this session runs inside Herdr. Control panes/agents/workspaces
  through the `herdr` CLI and load `herdr --skill` for its interface instead of
  guessing. Don't try to control a Herdr session from outside one.
- Long-running commands inside Herdr can be prefixed with `hnotify` to raise a
  notification when they finish (defined by the shell config).

## Guardrails

- `??` and `?sh` are interactive helpers for the human; don't call them from
  automation.
- Shell history is shared and persistent; don't put secrets on command lines.
  Config files may hold credentials — don't print or commit their contents.
