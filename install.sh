#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# install.sh — remote bootstrap for the AI harness genesis repository.
#
# Fetches (clones or updates) the genesis repo into a local cache, then renders
# a tailored harness into the target project via bootstrap.sh --auto-detect.
#
# Usage (from inside the project you want to tailor):
#   bash install.sh                      # render into the current directory
#   bash install.sh --output-dir /path   # render into a specific directory
#   bash install.sh --fetch-only         # just clone/update the cache, print its path
#   bash install.sh --ref some-branch    # use a non-default branch/tag
#
# This script is self-contained: it can be run from a clone of the cache
# (e.g. `bash ~/.cache/genesis/install.sh`) or piped from a raw
# URL if the repo is public (`curl -fsSL <raw>/install.sh | bash`).
#
# Environment overrides:
#   GENESIS_CACHE   where to clone the genesis repo (default: ~/.cache/genesis)
#   GENESIS_REF     branch/tag to check out (default: main)
# ─────────────────────────────────────────────────────────────────────────────

REPO_URL="https://github.com/hybridindie/genesis.git"

CACHE="${GENESIS_CACHE:-$HOME/.cache/genesis}"
REF="${GENESIS_REF:-main}"
OUTPUT_DIR="$PWD"
FETCH_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --ref)        REF="$2"; shift 2 ;;
    --cache)      CACHE="$2"; shift 2 ;;
    --fetch-only) FETCH_ONLY=1; shift 1 ;;
    -h|--help)    grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

log() { printf '%s\n' "$*" >&2; }

fetch_genesis() {
  if [[ -d "$CACHE/.git" ]]; then
    log "→ Updating genesis cache at $CACHE (ref: $REF)"
    git -C "$CACHE" fetch --quiet origin "$REF"
    git -C "$CACHE" checkout --quiet "$REF"
    git -C "$CACHE" pull --ff-only --quiet origin "$REF"
    return 0
  fi

  log "→ Cloning genesis repo into $CACHE (ref: $REF)"
  mkdir -p "$(dirname "$CACHE")"
  if git clone --quiet --depth 1 --branch "$REF" "$REPO_URL" "$CACHE"; then
    return 0
  fi
  log "ERROR: could not clone $REPO_URL — check your network connection and that git is installed."
  exit 1
}

fetch_genesis

if [[ $FETCH_ONLY -eq 1 ]]; then
  # Print the cache path on stdout so callers can capture it.
  printf '%s\n' "$CACHE"
  exit 0
fi

BOOTSTRAP="$CACHE/templates/scripts/bootstrap.sh"
if [[ ! -f "$BOOTSTRAP" ]]; then
  log "ERROR: bootstrap.sh not found at $BOOTSTRAP — cache may be corrupt. Delete $CACHE and retry."
  exit 1
fi

log "→ Rendering harness into $OUTPUT_DIR"
bash "$BOOTSTRAP" --auto-detect --output-dir "$OUTPUT_DIR"

log ""
log "✅ Harness rendered into $OUTPUT_DIR"
log "   Review CLAUDE.md / AGENTS.md, then commit: git add . && git commit -m 'chore: install AI harness'"
