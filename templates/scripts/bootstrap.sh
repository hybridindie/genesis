#!/bin/bash
# Render the genesis harness into a project. Thin wrapper over render.py; run
# `bootstrap.sh --help` for the flags.
#
#   bash templates/scripts/bootstrap.sh --auto-detect --output-dir ../myproject
#   bash templates/scripts/bootstrap.sh --output-dir ../api --stacks fastapi,frontend --packs production
#   bash templates/scripts/bootstrap.sh --output-dir ../game --add-stacks rust   # extend an installed harness
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/render.py" "$@"
