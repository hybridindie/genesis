#!/bin/bash
set -euo pipefail
shopt -s globstar nullglob

# Check that .claude/agents/*.md and .claude/rules/**/*.md stack version claims
# match the canonical context (AGENTS.md, falling back to CLAUDE.md).

ERRORS=0

CONTEXT=AGENTS.md
[[ -f $CONTEXT ]] || CONTEXT=CLAUDE.md
if [[ ! -f $CONTEXT ]]; then
  echo "FAIL: neither AGENTS.md nor CLAUDE.md found in the project root"
  exit 1
fi

# Extract stack versions (BSD/GNU portable; no grep -P)
PYTHON_V=$(sed -n 's/.*Python \([0-9][0-9.]*\).*/\1/p' "$CONTEXT" | head -1)
FASTAPI_V=$(sed -n 's/.*FastAPI \([0-9][0-9.+]*\).*/\1/p' "$CONTEXT" | head -1)
REACT_V=$(sed -n 's/.*React \([0-9][0-9.]*\).*/\1/p' "$CONTEXT" | head -1)
TS_V=$(sed -n 's/.*TypeScript \([0-9][0-9.]*\).*/\1/p' "$CONTEXT" | head -1)
VITE_V=$(sed -n 's/.*Vite \([0-9][0-9.]*\).*/\1/p' "$CONTEXT" | head -1)

for f in .claude/agents/*.md .claude/rules/**/*.md; do
  [[ -f "$f" ]] || continue
  # Simple grep for version contradictions (heuristic)
  if grep -q "Python 3\.11" "$f" && [[ "$PYTHON_V" != "3.11" ]]; then
    echo "AGENT-DRIFT: $f claims Python 3.11 but $CONTEXT says Python $PYTHON_V"
    ERRORS=$((ERRORS + 1))
  fi
  if grep -q "FastAPI 0\.10" "$f" && [[ "$FASTAPI_V" != "0.10"* ]]; then
    echo "AGENT-DRIFT: $f claims FastAPI 0.10 but $CONTEXT says FastAPI $FASTAPI_V"
    ERRORS=$((ERRORS + 1))
  fi
done

if [[ $ERRORS -gt 0 ]]; then
  echo "FAIL: $ERRORS agent drift issue(s) found."
  exit 1
fi

echo "PASS: Agent versions consistent with $CONTEXT."
