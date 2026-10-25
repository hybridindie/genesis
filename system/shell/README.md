# zsh configuration (system layer)

Rendered by `system/install.sh` into `~/.config/zsh`. `$HOME/.zshenv`,
`$HOME/.zprofile` and `$HOME/.zshrc` are one-line loaders that source it —
nothing else should be edited in `$HOME`.

Edit the source here and re-run the installer. Review with `--diff` first;
adopt with `--force` (timestamped backups).

## Layers

| File | Loaded by | Contents |
|------|-----------|----------|
| `zshenv` | **every** zsh (incl. `zsh -c` spawned by agents, IDEs, MCP servers) | PATH (de-duplicated), XDG vars, locale, `EDITOR`, pager. Silent — never prints. |
| `zprofile` | login shells | Homebrew environment (macOS/Linuxbrew), PATH re-dedupe. |
| `zshrc` | interactive shells | loads `conf.d/*.zsh` in lexical order |

## conf.d (load order)

| Module | Purpose |
|--------|---------|
| `00-options.zsh` | `setopt` defaults, macOS `ls` colours, bat man pager |
| `05-pyenv.zsh` | pyenv shell integration when installed (cached) |
| `10-history.zsh` | 200k history, shared, deduped, verified |
| `20-plugins.zsh` | zinit, plugins, generated completions, `compinit` cache |
| `30-completion.zsh` | completion styling + fzf-tab previews |
| `40-keybindings.zsh` | keymaps, **smart Tab** (partial accept), Ctrl+Space |
| `50-prompt.zsh` | starship |
| `60-integrations.zsh` | direnv + zoxide (and the `cd` wrapper) |
| `70-aliases.zsh` | aliases, guarded and platform-aware |
| `80-agents.zsh` | `??` / `?sh` helpers, `command_not_found_handler`, herdr helpers |
| `98-machine.zsh` | **generated** from installer flags (dev root, label, optional vault) |
| `99-local.zsh` | user-owned machine tweaks — created once, never overwritten |

## Platforms

macOS and Linux. Homebrew is found at `/opt/homebrew` or
`/home/linuxbrew/.linuxbrew`; `ls` colours and package hints branch on `$OSTYPE`.
Every optional tool is guarded with `$+commands[...]`, so a machine without
pyenv, zinit, eza, bat, fzf, zoxide, direnv, starship or herdr still gets a working
shell instead of errors.

## Rules of thumb

- `zshenv` must stay silent and free of interactive-only init; agent harnesses
  read its exit status and stdout.
- Anything added to `fpath` must happen before `compinit` in `20-plugins.zsh`.
- `fzf` is initialised in `20-plugins.zsh` and `40-keybindings.zsh` binds `^I`
  last: fzf captures the previous Tab binding as its fallback, so the `**` walk
  trigger keeps working while Tab still does partial accept first.
- Generated completions are cached in `~/.cache/zsh/completions` and rebuilt when
  the binary is newer; the `compinit` dump is rebuilt when it is >24 h old or a
  completion file is newer, and it is deleted first because `compinit` can
  otherwise skip the rescan.
