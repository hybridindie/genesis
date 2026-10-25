# System layer

Turns a new machine into a working workstation: the zsh config, the user-level
agent rules (OpenCode + Claude Code), shared git settings, and optional Herdr/
Zed config. `install.sh` renders these into the target home; the rendered copies
are the machine's source of truth.

```
system/
  install.sh          render into $HOME (idempotent, backs up on --force)
  shell/              zsh config -> ~/.config/zsh + $HOME loaders
  agents/             AGENTS.md (user-level), CLAUDE.md import, opencode.jsonc, settings.json
  git/                shared gitconfig + global gitignore
  herdr/config.toml   optional, installed when herdr is present
  zed/settings.json   optional, installed when zed is present
  bin/zed-wait        blocking editor wrapper -> ~/.local/bin
  Brewfile            macOS/Linuxbrew package set
```

## Install

```bash
bash system/install.sh \
  --dev-root ~/Development \
  --machine-label "$(hostname -s)" \
  [--wiki-fabric-dir ~/vault]
```

Flags: `--home` (test target), `--force` (update differing files after a
timestamped backup), `--diff` (show changes, write nothing), `--all` (install
agent/editor configs even when the tool is absent), `--no-tools` (skip the
tooling report), `--skip shell,agents,git,herdr,zed,bin,brewfile`.

Safety rules:

- A file that already exists and differs is **kept and reported**; `--force`
  backs it up as `<file>.bak-YYYYmmdd-HHMMSS` before replacing it.
- `conf.d/99-local.zsh` is user-owned: created once, never overwritten.
- `conf.d/98-machine.zsh` is generated from the flags on every run.
- `~/.gitconfig` is never rewritten: the installer only appends an `[include]`
  for `~/.config/system/gitconfig` when it is absent.

## Platforms

macOS and Linux. Homebrew is detected at `/opt/homebrew` or
`/home/linuxbrew/.linuxbrew`; the tooling report switches to `apt`/`dnf`/`pacman`
hints when brew is absent. Delta is optional: without `git-delta` the shared
gitconfig omits the pager instead of breaking `git diff`.

## After installing

```bash
exec zsh -l                 # reload the shell
brew bundle --file ~/.config/system/Brewfile   # macOS/Linuxbrew, optional
```

Then create a project — see [`../SYSTEM.md`](../SYSTEM.md).
