#!/usr/bin/env bash
# system/install.sh — render the workstation layer into a home directory.
#
# Usage:
#   bash system/install.sh [options]
#
# Options:
#   --home <dir>             target home (default: $HOME; used by CI)
#   --dev-root <dir>         development root (default: <home>/Development)
#   --machine-label <name>   label for the global AGENTS.md (default: hostname -s)
#   --wiki-fabric-dir <dir>  optional knowledge-fabric checkout
#   --force                  update files that differ (timestamped backup first)
#   --diff                   show what would change; write nothing
#   --all                    install agent/herdr/zed configs even if the tool is absent
#   --no-tools               skip the tooling report
#   --skip <a,b,...>         skip components: shell,agents,git,herdr,zed,bin,brewfile
#   -h, --help               show this help
#
# Existing files are never overwritten silently: a differing file is kept and
# reported; --force backs it up as <file>.bak-YYYYmmdd-HHMMSS before writing.
# conf.d/99-local.zsh is user-owned and is only created when missing.
# conf.d/98-machine.zsh is generated from the flags above.
set -euo pipefail

SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SELF_DIR/.." && pwd)"

TARGET_HOME="${HOME}"
DEV_ROOT=""
MACHINE_LABEL="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo machine)"
WIKI_FABRIC_DIR=""
FORCE=0
DIFF_ONLY=0
INSTALL_ALL=0
CHECK_TOOLS=1
SKIP=""

usage() {
  sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
}
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }
display() {
  case "$1" in
    "$TARGET_HOME")   printf '~' ;;
    "$TARGET_HOME"/*) printf '~%s' "${1#"$TARGET_HOME"}" ;;
    *)                printf '%s' "$1" ;;
  esac
}

while (( $# )); do
  case "$1" in
    --home)            TARGET_HOME="${2:?--home needs a directory}"; shift 2 ;;
    --dev-root)        DEV_ROOT="${2:?--dev-root needs a directory}"; shift 2 ;;
    --machine-label)   MACHINE_LABEL="${2:?--machine-label needs a value}"; shift 2 ;;
    --wiki-fabric-dir) WIKI_FABRIC_DIR="${2:?--wiki-fabric-dir needs a directory}"; shift 2 ;;
    --force)           FORCE=1; shift ;;
    --diff)            DIFF_ONLY=1; shift ;;
    --all)             INSTALL_ALL=1; shift ;;
    --no-tools)        CHECK_TOOLS=0; shift ;;
    --skip)            SKIP="${2:?--skip needs a list}"; shift 2 ;;
    -h|--help)         usage; exit 0 ;;
    *)                 die "unknown option: $1 (try --help)" ;;
  esac
done

[[ -n $TARGET_HOME ]] || die "--home must not be empty"
mkdir -p -- "$TARGET_HOME"
TARGET_HOME="$(cd -- "$TARGET_HOME" && pwd)"
DEV_ROOT="${DEV_ROOT:-$TARGET_HOME/Development}"

skipping() { [[ ",$SKIP," == *",$1,"* ]]; }
have_or_all() { (( INSTALL_ALL )) || command -v "$1" >/dev/null 2>&1 || [[ -d $2 ]]; }

# Render-time values -----------------------------------------------------------
if command -v delta >/dev/null 2>&1; then
  GIT_PAGER_LINE=$'\tpager = delta'
  DELTA_BLOCK=$'[interactive]\n\tdiffFilter = delta --color-only\n[delta]\n\tnavigate = true\n\tline-numbers = true\n\tsyntax-theme = Monokai Extended\n\thyperlinks = true'
else
  GIT_PAGER_LINE=$'\t# pager = delta   # install git-delta to enable'
  DELTA_BLOCK=""
fi

render() { # <src> <dst>
  local src=$1 dst=$2 content
  content=$(<"$src")
  content=${content//'{{MACHINE_LABEL}}'/$MACHINE_LABEL}
  content=${content//'{{DEV_ROOT}}'/$DEV_ROOT}
  content=${content//'{{GIT_PAGER_LINE}}'/$GIT_PAGER_LINE}
  content=${content//'{{DELTA_BLOCK}}'/$DELTA_BLOCK}
  printf '%s\n' "$content" > "$dst"
}

backup() {
  local f=$1 ts
  ts=$(date +%Y%m%d-%H%M%S)
  mv -- "$f" "$f.bak-$ts"
  say "  backed up $(display "$f") -> $(display "$f.bak-$ts")"
}

install_file() { # <src> <dst> [generated]
  local src=$1 dst=$2 mode=${3:-normal} tmp shown target
  tmp=$(mktemp "${TMPDIR:-/tmp}/genesis.XXXXXX")
  render "$src" "$tmp"
  shown=$(display "$dst")
  if [[ ! -e $dst && ! -L $dst ]]; then
    if (( DIFF_ONLY )); then
      say "would create $shown"
    else
      mkdir -p -- "$(dirname -- "$dst")"
      cp -- "$tmp" "$dst"
      say "created $shown"
    fi
  elif cmp -s -- "$tmp" "$dst" 2>/dev/null; then
    say "unchanged $shown"
  elif [[ -L $dst ]]; then
    target=$(readlink "$dst")
    if (( FORCE )) || [[ $mode == generated ]]; then
      if (( DIFF_ONLY )); then
        say "would replace symlink $shown -> $target with a regular file"
        diff -u -- "$dst" "$tmp" || true
      else
        say "warning: $shown is a symlink -> $target; replacing it with a regular file"
        backup "$dst"
        cp -- "$tmp" "$dst"
        say "updated $shown"
      fi
    else
      say "differs (symlink kept) $shown -> $target — reconcile the link target or re-run with --force"
      if (( DIFF_ONLY )); then diff -u -- "$dst" "$tmp" || true; fi
    fi
  elif (( FORCE )) || [[ $mode == generated ]]; then
    if (( DIFF_ONLY )); then
      say "would update $shown"
      diff -u -- "$dst" "$tmp" || true
    else
      backup "$dst"
      cp -- "$tmp" "$dst"
      say "updated $shown"
    fi
  else
    say "differs (kept) $shown — re-run with --force to update"
    if (( DIFF_ONLY )); then diff -u -- "$dst" "$tmp" || true; fi
  fi
  rm -f -- "$tmp"
}

install_if_missing() { # <src> <dst>
  local src=$1 dst=$2 tmp shown
  shown=$(display "$dst")
  if [[ -e $dst || -L $dst ]]; then
    say "kept (user-owned) $shown"
    return
  fi
  tmp=$(mktemp "${TMPDIR:-/tmp}/genesis.XXXXXX")
  render "$src" "$tmp"
  if (( DIFF_ONLY )); then
    say "would create $shown"
  else
    mkdir -p -- "$(dirname -- "$dst")"
    cp -- "$tmp" "$dst"
    say "created $shown"
  fi
  rm -f -- "$tmp"
}

write_machine() {
  local dst="$TARGET_HOME/.config/zsh/conf.d/98-machine.zsh" tmp shown
  tmp=$(mktemp "${TMPDIR:-/tmp}/genesis.XXXXXX")
  {
    printf '# Generated by system/install.sh — machine values.\n'
    printf '# Re-run the installer to change these; personal tweaks go in 99-local.zsh.\n'
    printf 'export DEV_ROOT=%q\n' "$DEV_ROOT"
    printf 'export MACHINE_LABEL=%q\n' "$MACHINE_LABEL"
    if [[ -n $WIKI_FABRIC_DIR ]]; then
      printf 'export WIKI_FABRIC_DIR=%q\n' "$WIKI_FABRIC_DIR"
    fi
  } > "$tmp"
  shown=$(display "$dst")
  if [[ -f $dst ]] && cmp -s -- "$tmp" "$dst"; then
    say "unchanged $shown"
  elif (( DIFF_ONLY )); then
    say "would write $shown"
  else
    mkdir -p -- "$(dirname -- "$dst")"
    cp -- "$tmp" "$dst"
    say "wrote $shown"
  fi
  rm -f -- "$tmp"
}

ensure_git_include() {
  local gc="$TARGET_HOME/.gitconfig"
  local line='path = ~/.config/system/gitconfig' shown
  shown=$(display "$gc")
  if [[ -f $gc ]] && grep -qF -- "$line" "$gc"; then
    say "unchanged $shown include"
    return
  fi
  if (( DIFF_ONLY )); then
    say "would add [include] to $shown"
    return
  fi
  if [[ -f $gc ]] && grep -q '^\[include\]' "$gc"; then
    say "note: $shown already has an [include] section; add manually:"
    say "        $line"
    return
  fi
  mkdir -p -- "$(dirname -- "$gc")"
  if [[ -f $gc ]]; then printf '\n' >> "$gc"; fi
  printf '[include]\n\t%s\n' "$line" >> "$gc"
  say "updated $shown include"
}

install_shell() {
  say "== shell"
  local f base
  for f in zshenv zprofile zshrc; do
    install_file "$SELF_DIR/shell/$f" "$TARGET_HOME/.config/zsh/$f"
  done
  for f in "$SELF_DIR"/shell/conf.d/*.zsh; do
    [[ -e $f ]] || continue
    base=$(basename "$f")
    if [[ $base == 99-local.zsh ]]; then
      install_if_missing "$f" "$TARGET_HOME/.config/zsh/conf.d/$base"
    else
      install_file "$f" "$TARGET_HOME/.config/zsh/conf.d/$base"
    fi
  done
  write_machine
  for f in zshenv zprofile zshrc profile; do
    install_file "$SELF_DIR/shell/home/$f" "$TARGET_HOME/.$f"
  done
}

install_agents() {
  say "== agents"
  install_file "$SELF_DIR/agents/AGENTS.md" "$TARGET_HOME/.config/opencode/AGENTS.md"
  if have_or_all claude "$TARGET_HOME/.claude"; then
    install_file "$SELF_DIR/agents/CLAUDE.md" "$TARGET_HOME/.claude/CLAUDE.md"
    install_file "$SELF_DIR/agents/settings.json" "$TARGET_HOME/.claude/settings.json"
  else
    say "skipped Claude config (claude not installed; use --all to force)"
  fi
  if have_or_all opencode "$TARGET_HOME/.config/opencode"; then
    install_file "$SELF_DIR/agents/opencode.jsonc" "$TARGET_HOME/.config/opencode/opencode.jsonc"
  else
    say "skipped OpenCode config (opencode not installed; use --all to force)"
  fi
}

install_git() {
  say "== git"
  install_file "$SELF_DIR/git/gitconfig" "$TARGET_HOME/.config/system/gitconfig"
  install_file "$SELF_DIR/git/ignore" "$TARGET_HOME/.config/git/ignore"
  ensure_git_include
}

install_herdr() {
  say "== herdr"
  if have_or_all herdr "$TARGET_HOME/.config/herdr"; then
    install_file "$SELF_DIR/herdr/config.toml" "$TARGET_HOME/.config/herdr/config.toml"
  else
    say "skipped herdr config (herdr not installed; use --all to force)"
  fi
}

install_zed() {
  say "== zed"
  if have_or_all zed "$TARGET_HOME/.config/zed"; then
    install_file "$SELF_DIR/zed/settings.json" "$TARGET_HOME/.config/zed/settings.json"
  else
    say "skipped zed settings (zed not installed; use --all to force)"
  fi
}

install_bin() {
  say "== bin"
  install_file "$SELF_DIR/bin/zed-wait" "$TARGET_HOME/.local/bin/zed-wait"
  [[ -e $TARGET_HOME/.local/bin/zed-wait ]] && chmod +x "$TARGET_HOME/.local/bin/zed-wait"
}

install_brewfile() {
  say "== brewfile"
  install_file "$SELF_DIR/Brewfile" "$TARGET_HOME/.config/system/Brewfile"
}

check_tools() {
  local missing=() t
  for t in zsh git rg fd eza bat yq delta direnv fzf zoxide starship uv gh zed opencode claude herdr kubectl docker; do
    command -v "$t" >/dev/null 2>&1 || missing+=("$t")
  done
  say "== tools"
  if (( ${#missing[@]} == 0 )); then
    say "all expected tools present"
    return
  fi
  say "missing: ${missing[*]}"
  if command -v brew >/dev/null 2>&1; then
    say "  install: brew bundle --file $(display "$TARGET_HOME/.config/system/Brewfile")"
  elif command -v apt >/dev/null 2>&1; then
    say "  install: sudo apt install ${missing[*]}"
  elif command -v dnf >/dev/null 2>&1; then
    say "  install: sudo dnf install ${missing[*]}"
  elif command -v pacman >/dev/null 2>&1; then
    say "  install: sudo pacman -S ${missing[*]}"
  else
    say "  install each with your platform package manager"
  fi
  say "  (optional: herdr, zed, kubectl, docker)"
}

say "genesis system install"
say "  target home: $(display "$TARGET_HOME")"
say "  dev root:    $DEV_ROOT"
say "  machine:     $MACHINE_LABEL"
(( FORCE )) && say "  mode:        force (differing files are backed up and replaced)"
(( DIFF_ONLY )) && say "  mode:        diff (nothing is written)"
say

skipping shell    || install_shell
skipping agents   || install_agents
skipping git      || install_git
skipping herdr    || install_herdr
skipping zed      || install_zed
skipping bin      || install_bin
skipping brewfile || install_brewfile

if (( CHECK_TOOLS )); then
  say
  check_tools
fi

say
say "next:"
say "  1. restart the shell (exec zsh -l) or open a new terminal"
say "  2. review ~/.config/opencode/AGENTS.md and ~/.claude/CLAUDE.md"
say "  3. create a project: $REPO_ROOT/new-project.sh ../myapp --profile mcp"
