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
  bin/graphify-gdscript  teaches the machine's graphify to parse GDScript -> ~/.local/bin
                         (only with graphify installed and a Godot project under --dev-root)
  Brewfile            macOS/Linuxbrew package set
```

## Install

```bash
bash system/install.sh \
  --dev-root ~/Development \
  --machine-label "$(hostname -s)"
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

### One writer per path

The installer writes regular files. If `$HOME/.zshenv`,
`$HOME/.claude/settings.json` or another target is a symlink into a separate
dotfiles repo, it keeps the link unless the content differs; `--force` then
backs up and replaces the link with a regular file. Pick one owner per path —
either this installer or the dotfiles links — and keep machine-only values in
`conf.d/99-local.zsh` or the dotfiles overlay. Do not run both update paths over
the same file.

Project configs carry the portable permission baseline; the machine-level
OpenCode/Claude configs add the global denies (SSH, cloud credentials, `.env`).
OpenCode appends global permissions before project permissions, so the machine
rules remain the outer guardrail.

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
