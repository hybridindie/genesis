#!/usr/bin/env bash
# new-project.sh — create a project and render the genesis harness into it.
#
# Usage:
#   ./new-project.sh <path> [bootstrap.sh flags...]
#
# Without extra flags the harness is tailored with --auto-detect (it probes the
# directory). Pass any bootstrap flag to override, e.g.:
#   ./new-project.sh ../mcp-server --stacks mcp
#   ./new-project.sh ../api --project-name "My API" --stacks fastapi,frontend --packs production
#   ./new-project.sh ../cli --stacks python --scaffold
#
# The script creates the directory, initialises git (main) when needed, renders
# the harness, installs the tracked git hooks (unless --no-hooks), optionally
# writes the repo-hygiene skeleton (--scaffold), and prints the next steps. It
# never commits and never pushes.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
}

target="${1:-}"
if [[ -z $target || $target == -h || $target == --help ]]; then
  usage
  exit 0
fi
shift

mkdir -p -- "$target"
target="$(cd -- "$target" && pwd)"

install_hooks=1
scaffold=0
args=()
for arg in "$@"; do
  case "$arg" in
    --no-hooks) install_hooks=0 ;;
    --scaffold) scaffold=1 ;;
    *) args+=("$arg") ;;
  esac
done

if [[ ! -d $target/.git ]]; then
  git -C "$target" init -q -b main
  printf 'initialised git repository in %s\n' "$target"
fi

if (( ${#args[@]} )); then
  bash "$REPO_ROOT/templates/scripts/bootstrap.sh" --output-dir "$target" "${args[@]}"
else
  bash "$REPO_ROOT/templates/scripts/bootstrap.sh" --auto-detect --output-dir "$target"
fi

if (( scaffold )); then
  python3 "$REPO_ROOT/templates/scripts/scaffold.py" --root "$target"
fi

if (( install_hooks )) && [[ -d $target/.githooks ]]; then
  if ! (cd "$target" && bash .claude/hooks/install-git-hooks.sh); then
    printf 'git hooks not installed; run: cd %s && bash .claude/hooks/install-git-hooks.sh\n' "$target"
  fi
fi

cat <<EOF

next steps:
  cd $target
  review CLAUDE.md, AGENTS.md and .claude/rules/
  run /harness-eval, then /customize-harness (in Claude Code or Opencode)
  git add -A && git commit -m "chore: initial AI harness"
EOF
