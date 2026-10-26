# Genesis: machine → project

This repository has two layers. The **system** layer configures the machine; the
**project** layer renders an instruction harness into a repository.

```
machine                                    project
───────                                    ───────
system/install.sh                          install.sh  /  new-project.sh
  ├─ ~/.config/zsh          (shell)          ├─ .claude/rules/  .claude/skills/
  ├─ ~/.config/opencode/AGENTS.md (user)     ├─ .opencode/{skills,agents,commands}
  ├─ ~/.claude/{CLAUDE.md,settings.json}     ├─ .claude/{rules,skills,hooks}
  ├─ ~/.config/system/gitconfig (git)        ├─ CLAUDE.md  AGENTS.md
  └─ herdr / zed (optional)                  └─ my-workflows.md
```

## 1. New machine

```bash
git clone https://github.com/hybridindie/genesis.git ~/genesis
cd ~/genesis
bash system/install.sh --dev-root ~/Development --machine-label "$(hostname -s)"
exec zsh -l
```

Optional, per platform:

```bash
brew bundle --file ~/.config/system/Brewfile   # macOS / Linuxbrew
sudo apt install zsh ripgrep fd-find bat direnv fzf zoxide   # Debian/Ubuntu
```

The installer reports which tools are missing and the right command for the
platform. It never installs anything on its own.

## 2. New project

```bash
cd ~/Development
~/genesis/new-project.sh myapp            # git init + auto-detect + render
~/genesis/new-project.sh mcp-server --profile mcp
~/genesis/new-project.sh cli --profile python --scaffold  # + README/LICENSE/Makefile/skeleton
```

`new-project.sh` creates the directory, runs `git init -b main`, renders the
harness with `templates/scripts/bootstrap.sh`, installs the tracked `.githooks`
unless `--no-hooks`, and prints the next steps. Bootstrap adds
`.github/workflows/ci.yml` only when the project has no workflow yet. To patch
an existing repository instead:

```bash
bash ~/genesis/install.sh            # from inside the project (auto-detect)
```

## 3. Tailor the project

```
bootstrap.sh        → render (deterministic: placeholders, overlays, conditionals)
      ↓
/harness-eval       → agent reads the code, trims rules that do not apply,
                      suggests rules the stack needs
      ↓
/customize-harness  → weaves my-workflows.md (now filled with your shell,
                      tooling, direnv and permission conventions) into the
                      project's CLAUDE.md / AGENTS.md
```

## 4. What lives where

| Concern | Location | Source of truth |
|---|---|---|
| Shell, git defaults, user-level agent rules | machine (`~/.config/...`) | this repo, rendered by `system/install.sh` |
| Per-machine tweaks, secrets, personal skills | machine (`conf.d/99-local.zsh`, `~/.envrc`, private dotfiles repo) | the machine |
| Project rules (`Articles I–X`, agents, commands, skills) | target repo | this repo, rendered by `bootstrap.sh` |
| Project-specific tailoring | target repo | the project (never edit `templates/`) |

One path, one writer: if a private dotfiles repo symlinks `~/.zshenv`,
`~/.claude/settings.json`, `~/.local/bin/zed-wait` or the shared git config, do
not also update the same path from this installer. Choose the installer or the
dotfiles links, and keep machine-only values in `99-local.zsh` / the dotfiles
overlay.

## Updating

```bash
git -C ~/genesis pull
bash ~/genesis/system/install.sh --diff     # review machine changes
bash ~/genesis/system/install.sh --force    # adopt them (timestamped backups)
```

For projects, re-run `bootstrap.sh` (or `/harness-eval` + `/customize-harness`)
after pulling, so rule changes propagate.

## Rules of engagement

- The installer never overwrites a differing file without `--force`, and never
  touches secrets or `~/.gitconfig` identity.
- A project's rendered harness is owned by that project; re-rendering is a
  deliberate update, not a background sync.
- Machine-specific values are flags (`--dev-root`, `--machine-label`,
  `--wiki-fabric-dir`), never hardcoded in this repo.
