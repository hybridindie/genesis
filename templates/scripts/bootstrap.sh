#!/bin/bash
set -euo pipefail

# Harness Bootstrap Script
# Renders AI assistant harness templates for a new project.
#
# Usage:
#   bash templates/scripts/bootstrap.sh \
#     --project-name "MyProject" \
#     --project-slug "myproject" \
#     --output-dir "../myproject"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$(dirname "$SCRIPT_DIR")"

# ... CLI parsing and defaults remain unchanged ...
# [CLI defaults truncated for brevity - same as before]
PROJECT_NAME=""
PROJECT_SLUG=""
BACKEND_PATH="backend"
FRONTEND_PATH="frontend"
REPO_ORG=""
REPO_NAME=""
DB_PROVIDER="supabase"
STATE_MANAGER="zustand"
PYTHON_VERSION="3.12"
FASTAPI_VERSION="0.119+"
REACT_VERSION="19"
TYPESCRIPT_VERSION="5.9"
VITE_VERSION="7.3"
PKG_MANAGER_BACKEND="uv"
PKG_MANAGER_FRONTEND="npm"
COVERAGE_AGGREGATE_BACKEND="70"
COVERAGE_AGGREGATE_FRONTEND="60"
CALVER_VERSION=""
ARTICLE_I_SERVICE_EXAMPLES="auth_manager, analytics_engine, content_manager"
FRONTEND_STORE_EXAMPLES="auth, analytics, content"
DB_EXTENSIONS="pgvector, pgmq, HSTORE"
HAS_MLFLOW="no"
HAS_LANGGRAPH="no"
CICD_PLATFORM="github-actions"
E2E_TOOL="playwright"
UI_LIBRARY="shadcn/ui"
TAILWIND="yes"
ZOD_VALIDATION="yes"
CUSTOM_INSTRUCTIONS=""
CUSTOM_TECH_STACK=""
OUTPUT_DIR=""
WITH_CI=1
FORCE_CI=0
FORCE_HOOKS=0

# ── Auto-detect support ──
MODE="full"
PROFILE=""
PROFILE_GIVEN=0
AUTO_DETECT=0
AUTO_JSON=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --backend-path) BACKEND_PATH="$2"; shift 2 ;;
    --frontend-path) FRONTEND_PATH="$2"; shift 2 ;;
    --repo-org) REPO_ORG="$2"; shift 2 ;;
    --repo-name) REPO_NAME="$2"; shift 2 ;;
    --db-provider) DB_PROVIDER="$2"; shift 2 ;;
    --state-manager) STATE_MANAGER="$2"; shift 2 ;;
    --python-version) PYTHON_VERSION="$2"; shift 2 ;;
    --fastapi-version) FASTAPI_VERSION="$2"; shift 2 ;;
    --react-version) REACT_VERSION="$2"; shift 2 ;;
    --typescript-version) TYPESCRIPT_VERSION="$2"; shift 2 ;;
    --vite-version) VITE_VERSION="$2"; shift 2 ;;
    --pkg-manager-backend) PKG_MANAGER_BACKEND="$2"; shift 2 ;;
    --pkg-manager-frontend) PKG_MANAGER_FRONTEND="$2"; shift 2 ;;
    --coverage-aggregate-backend) COVERAGE_AGGREGATE_BACKEND="$2"; shift 2 ;;
    --coverage-aggregate-frontend) COVERAGE_AGGREGATE_FRONTEND="$2"; shift 2 ;;
    --calver-version) CALVER_VERSION="$2"; shift 2 ;;
    --article-i-services) ARTICLE_I_SERVICE_EXAMPLES="$2"; shift 2 ;;
    --frontend-stores) FRONTEND_STORE_EXAMPLES="$2"; shift 2 ;;
    --db-extensions) DB_EXTENSIONS="$2"; shift 2 ;;
    --has-mlflow) HAS_MLFLOW="$2"; shift 2 ;;
    --has-langgraph) HAS_LANGGRAPH="$2"; shift 2 ;;
    --cicd-platform) CICD_PLATFORM="$2"; shift 2 ;;
    --e2e-tool) E2E_TOOL="$2"; shift 2 ;;
    --ui-library) UI_LIBRARY="$2"; shift 2 ;;
    --tailwind) TAILWIND="$2"; shift 2 ;;
    --zod-validation) ZOD_VALIDATION="$2"; shift 2 ;;
    --custom-instructions) CUSTOM_INSTRUCTIONS="$2"; shift 2 ;;
    --custom-tech-stack) CUSTOM_TECH_STACK="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --profile) PROFILE="$2"; PROFILE_GIVEN=1; shift 2 ;;
    --auto-detect) AUTO_DETECT=1; shift 1 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --no-ci) WITH_CI=0; shift 1 ;;
    --force-ci) FORCE_CI=1; shift 1 ;;
    --force-hooks) FORCE_HOOKS=1; shift 1 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Profile detection ──
# One profile per project. Explicit --profile wins; otherwise infer from the
# target project.
detect_profile() {
  local dir="$1"
  [[ -n "$dir" ]] || dir="."
  if [[ -f "$dir/project.godot" ]]; then echo godot; return; fi
  if [[ -f "$dir/pyproject.toml" ]] && grep -qiE 'langgraph|mlflow' "$dir/pyproject.toml" 2>/dev/null; then
    echo agent; return
  fi
  if [[ -f "$dir/package.json" && -f "$dir/pyproject.toml" ]]; then echo web; return; fi
  if [[ -f "$dir/pyproject.toml" ]] && grep -qiE '(^|[^a-z])(fastmcp|mcp)([^a-z]|$)' "$dir/pyproject.toml" 2>/dev/null; then
    echo mcp; return
  fi
  echo python
}

# ── Auto-detect phase ──
if [[ $AUTO_DETECT -eq 1 ]]; then
  # Detect from current working directory
  DETECTED=$(python3 "$SCRIPT_DIR/inspect-project.py" "${OUTPUT_DIR:-$(pwd)}" 2>/dev/null || echo '{}')
  if [[ "$DETECTED" == '{}' || -z "$DETECTED" ]]; then
    echo "WARN: Auto-detect returned no results; using defaults"
  else
    # Extract values using python3 (jq might not be available)
    AUTO_MODE=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('mode','full'))" <<< "$DETECTED")
    AUTO_PROFILE=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('profile','') or '')" <<< "$DETECTED")
    AUTO_NAME=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project_name',''))" <<< "$DETECTED")
    AUTO_SLUG=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project_slug',''))" <<< "$DETECTED")
    PYTHON_VERSION=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('python_version',''); print(v if v else '3.12')" <<< "$DETECTED")
    FASTAPI_VERSION=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('fastapi_version',''); print(v if v else '0.119+')" <<< "$DETECTED")
    PKG_MANAGER_BACKEND=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pkg_manager_backend','uv'))" <<< "$DETECTED")
    DB_PROVIDER=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('db_provider',''); print(v if v else 'supabase')" <<< "$DETECTED")
    CICD_PLATFORM=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cicd_platform','github-actions'))" <<< "$DETECTED")
    HAS_MLFLOW=$(python3 -c "import sys,json; print('yes' if json.load(sys.stdin).get('has_mlflow',False) else 'no')" <<< "$DETECTED")
    HAS_LANGGRAPH=$(python3 -c "import sys,json; print('yes' if json.load(sys.stdin).get('has_langgraph',False) else 'no')" <<< "$DETECTED")

    # Frontend overrides (only if mode is NOT backend-only)
    if [[ "$AUTO_MODE" != "backend-only" ]]; then
      REACT_VERSION=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('react_version',''); print(v if v else '19')" <<< "$DETECTED")
      VITE_VERSION=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('vite_version',''); print(v if v else '7.3')" <<< "$DETECTED")
      STATE_MANAGER=$(python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('state_manager',''); print(v if v else 'zustand')" <<< "$DETECTED")
      TAILWIND=$(python3 -c "import sys,json; print('yes' if json.load(sys.stdin).get('tailwind',False) else 'no')" <<< "$DETECTED")
      ZOD_VALIDATION=$(python3 -c "import sys,json; print('yes' if json.load(sys.stdin).get('zod_validation',False) else 'no')" <<< "$DETECTED")
      PKG_MANAGER_FRONTEND=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pkg_manager_frontend','npm'))" <<< "$DETECTED")
    fi

    # Apply detected overrides only where CLI did not already specify
    if [[ -z "$MODE" || "$MODE" == "full" ]]; then
      MODE="$AUTO_MODE"
    fi
    if [[ -z "$PROFILE" ]]; then
      PROFILE="$AUTO_PROFILE"
    fi
    if [[ -z "$PROJECT_NAME" && -n "$AUTO_NAME" ]]; then
      PROJECT_NAME="$AUTO_NAME"
    fi
    if [[ -z "$PROJECT_SLUG" && -n "$AUTO_SLUG" ]]; then
      PROJECT_SLUG="$AUTO_SLUG"
    fi

    AUTO_JSON="$DETECTED"
    echo "Auto-detected: mode=$MODE profile=$PROFILE python=$PYTHON_VERSION"
  fi
fi

if (( ! PROFILE_GIVEN )); then
  PROFILE="$(detect_profile "$OUTPUT_DIR")"
fi

# Normalize legacy names and validate.
case "$PROFILE" in
  mcp|python|agent|web|godot) ;;
  fastapi|fastapi+react) PROFILE="web" ;;
  generic-python|"") PROFILE="python" ;;
  *) echo "ERROR: unknown profile '$PROFILE' (expected mcp|python|agent|web|godot)" >&2; exit 1 ;;
esac

# Fall back to the directory name when auto-detect produced no name/slug
# (e.g. a Godot project with no pyproject.toml).
if [[ -z "$PROJECT_NAME" && -n "$OUTPUT_DIR" ]]; then
  PROJECT_NAME="$(basename "$(cd "$OUTPUT_DIR" && pwd)")"
fi
if [[ -z "$PROJECT_SLUG" && -n "$PROJECT_NAME" ]]; then
  PROJECT_SLUG="$(printf '%s' "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')"
  PROJECT_SLUG="${PROJECT_SLUG#-}"; PROJECT_SLUG="${PROJECT_SLUG%-}"
fi

if [[ -z "$PROJECT_NAME" || -z "$PROJECT_SLUG" || -z "$OUTPUT_DIR" ]]; then
  echo "Usage: $0 --project-name <name> --project-slug <slug> --output-dir <dir> [options]"
  echo ""
  echo "Or auto-detect:"
  echo "  $0 --auto-detect --output-dir <dir>"
  exit 1
fi

# Profile hygiene: only web-app carries frontend/DB placeholders; only agent
# carries MLflow/LangGraph; godot has no Python toolchain commands.
if [[ "$PROFILE" != "web" ]]; then
  REACT_VERSION=""; TYPESCRIPT_VERSION=""; VITE_VERSION=""; STATE_MANAGER=""
  FRONTEND_PATH=""; E2E_TOOL=""; UI_LIBRARY=""; TAILWIND="no"; ZOD_VALIDATION="no"
  COVERAGE_AGGREGATE_FRONTEND=""; FRONTEND_STORE_EXAMPLES=""
fi
if [[ "$PROFILE" != "agent" ]]; then
  HAS_MLFLOW="no"; HAS_LANGGRAPH="no"
fi
if [[ "$PROFILE" == "godot" ]]; then
  PKG_MANAGER_BACKEND=""; TEST_BACKEND_CMD=""; LINT_BACKEND_CMD=""; TYPE_BACKEND_CMD=""
fi

if [[ -z "$REPO_ORG" ]]; then REPO_ORG="$PROJECT_SLUG"; fi
if [[ -z "$REPO_NAME" ]]; then REPO_NAME="$PROJECT_SLUG"; fi
if [[ -z "$CALVER_VERSION" ]]; then CALVER_VERSION="$(date +%Y.%m.%d)"; fi

# Derive DB conditionals from DB_PROVIDER
if [[ "$DB_PROVIDER" == "supabase" ]]; then
  HAS_SUPABASE="yes"
  HAS_POSTGRES="no"
elif [[ "$DB_PROVIDER" == "postgres" ]]; then
  HAS_SUPABASE="no"
  HAS_POSTGRES="yes"
else
  HAS_SUPABASE="no"
  HAS_POSTGRES="no"
fi

if [[ "$PKG_MANAGER_BACKEND" == "uv" ]]; then
  TEST_BACKEND_CMD="uv run pytest"
  LINT_BACKEND_CMD="uv run ruff check ."
  TYPE_BACKEND_CMD="uv run mypy src/"
else
  TEST_BACKEND_CMD="pytest"
  LINT_BACKEND_CMD="ruff check ."
  TYPE_BACKEND_CMD="mypy src/"
fi

if [[ "$PKG_MANAGER_FRONTEND" == "npm" ]]; then
  TEST_FRONTEND_CMD="npx vitest run"
  LINT_FRONTEND_CMD="npm run lint"
  TYPE_FRONTEND_CMD="npm run type-check"
elif [[ "$PKG_MANAGER_FRONTEND" == "bun" ]]; then
  TEST_FRONTEND_CMD="bun test"
  LINT_FRONTEND_CMD="bun run lint"
  TYPE_FRONTEND_CMD="bun run type-check"
else
  TEST_FRONTEND_CMD="npx vitest run"
  LINT_FRONTEND_CMD="npm run lint"
  TYPE_FRONTEND_CMD="npm run type-check"
fi

MIRROR_PAIRS="$TEMPLATES_DIR/_shared/mirror-pairs.json"

# Portable: use python3 to look up render_dir for a given filename
render_articles() {
  local src_root="$1" src rel
  [[ -d "$src_root" ]] || return 0
  while IFS= read -r src; do
    rel="${src#$src_root/}"
    substitute_placeholders "$src" "$OUTPUT_DIR/.claude/rules/$rel"
  done < <(find "$src_root" -type f -name '*.md' | sort)
}

substitute_placeholders() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  sed \
    -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
    -e "s|{{PROJECT_SLUG}}|$PROJECT_SLUG|g" \
    -e "s|{{BACKEND_PATH}}|$BACKEND_PATH|g" \
    -e "s|{{FRONTEND_PATH}}|$FRONTEND_PATH|g" \
    -e "s|{{REPO_ORG}}|$REPO_ORG|g" \
    -e "s|{{REPO_NAME}}|$REPO_NAME|g" \
    -e "s|{{PYTHON_VERSION}}|$PYTHON_VERSION|g" \
    -e "s|{{FASTAPI_VERSION}}|$FASTAPI_VERSION|g" \
    -e "s|{{REACT_VERSION}}|$REACT_VERSION|g" \
    -e "s|{{TYPESCRIPT_VERSION}}|$TYPESCRIPT_VERSION|g" \
    -e "s|{{VITE_VERSION}}|$VITE_VERSION|g" \
    -e "s|{{DB_PROVIDER}}|$DB_PROVIDER|g" \
    -e "s|{{STATE_MANAGER}}|$STATE_MANAGER|g" \
    -e "s|{{TEST_BACKEND_CMD}}|$TEST_BACKEND_CMD|g" \
    -e "s|{{TEST_FRONTEND_CMD}}|$TEST_FRONTEND_CMD|g" \
    -e "s|{{LINT_BACKEND_CMD}}|$LINT_BACKEND_CMD|g" \
    -e "s|{{LINT_FRONTEND_CMD}}|$LINT_FRONTEND_CMD|g" \
    -e "s|{{TYPE_BACKEND_CMD}}|$TYPE_BACKEND_CMD|g" \
    -e "s|{{TYPE_FRONTEND_CMD}}|$TYPE_FRONTEND_CMD|g" \
    -e "s|{{PKG_MANAGER_BACKEND}}|$PKG_MANAGER_BACKEND|g" \
    -e "s|{{PKG_MANAGER_FRONTEND}}|$PKG_MANAGER_FRONTEND|g" \
    -e "s|{{COVERAGE_AGGREGATE_BACKEND}}|$COVERAGE_AGGREGATE_BACKEND|g" \
    -e "s|{{COVERAGE_AGGREGATE_FRONTEND}}|$COVERAGE_AGGREGATE_FRONTEND|g" \
    -e "s|{{CALVER_VERSION}}|$CALVER_VERSION|g" \
    -e "s|{{ARTICLE_I_SERVICE_EXAMPLES}}|$ARTICLE_I_SERVICE_EXAMPLES|g" \
    -e "s|{{FRONTEND_STORE_EXAMPLES}}|$FRONTEND_STORE_EXAMPLES|g" \
    -e "s|{{DB_EXTENSIONS}}|$DB_EXTENSIONS|g" \
    -e "s|{{HAS_MLFLOW}}|$HAS_MLFLOW|g" \
    -e "s|{{HAS_LANGGRAPH}}|$HAS_LANGGRAPH|g" \
    -e "s|{{CICD_PLATFORM}}|$CICD_PLATFORM|g" \
    -e "s|{{E2E_TOOL}}|$E2E_TOOL|g" \
    -e "s|{{UI_LIBRARY}}|$UI_LIBRARY|g" \
    -e "s|{{TAILWIND}}|$TAILWIND|g" \
    -e "s|{{ZOD_VALIDATION}}|$ZOD_VALIDATION|g" \
    -e "s|{{CUSTOM_INSTRUCTIONS}}|$CUSTOM_INSTRUCTIONS|g" \
    -e "s|{{CUSTOM_TECH_STACK}}|$CUSTOM_TECH_STACK|g" \
    "$src" > "$dst"
}

render_harness() {
  local harness_dir="$1"
  local target_dir="$2"
  echo "Rendering $harness_dir -> $target_dir"
  find "$harness_dir" -type f | while read -r src; do
    rel="${src#$harness_dir/}"
    dst="$target_dir/$rel"
    substitute_placeholders "$src" "$dst"
  done
}

mkdir -p "$OUTPUT_DIR"

echo "=== Rendering Shared Articles ==="

# Core articles ship for every profile; the selected profile then adds or
# overrides them by relative path (e.g. profiles/web/articles/architecture.md).
render_articles "$TEMPLATES_DIR/_shared/core/articles"
render_articles "$TEMPLATES_DIR/_shared/profiles/$PROFILE/articles"

echo "=== Rendering Shared Agents ==="
if [[ -d "$TEMPLATES_DIR/_shared/agents" ]]; then
  mkdir -p "$OUTPUT_DIR/.claude/agents"
  for shared in "$TEMPLATES_DIR/_shared/agents/"*.md; do
    [[ -f "$shared" ]] || continue
    fname=$(basename "$shared")
    substitute_placeholders "$shared" "$OUTPUT_DIR/.claude/agents/$fname"
  done
fi

if [[ -d "$TEMPLATES_DIR/_shared/profiles/$PROFILE/agents" ]]; then
  mkdir -p "$OUTPUT_DIR/.claude/agents"
  for shared in "$TEMPLATES_DIR/_shared/profiles/$PROFILE/agents/"*.md; do
    [[ -f "$shared" ]] || continue
    substitute_placeholders "$shared" "$OUTPUT_DIR/.claude/agents/$(basename "$shared")"
  done
fi

echo "=== Rendering Shared Commands ==="
if [[ -d "$TEMPLATES_DIR/_shared/commands" ]]; then
  mkdir -p "$OUTPUT_DIR/.claude/commands"
  for shared in "$TEMPLATES_DIR/_shared/commands/"*.md; do
    [[ -f "$shared" ]] || continue
    fname=$(basename "$shared")
    substitute_placeholders "$shared" "$OUTPUT_DIR/.claude/commands/$fname"
  done
fi

if [[ -d "$TEMPLATES_DIR/_shared/profiles/$PROFILE/commands" ]]; then
  mkdir -p "$OUTPUT_DIR/.claude/commands"
  for shared in "$TEMPLATES_DIR/_shared/profiles/$PROFILE/commands/"*.md; do
    [[ -f "$shared" ]] || continue
    substitute_placeholders "$shared" "$OUTPUT_DIR/.claude/commands/$(basename "$shared")"
  done
fi

echo "=== Rendering Shared Doctrine ==="
# Doctrine files ship into .claude/rules/doctrine/ so articles and agents can
# reference them by path. They are not mirrored to OpenCode (referenced by
# articles/agents, not loaded as path-targeted instructions).
python3 -c "
import json, os
with open('$TEMPLATES_DIR/_shared/mirror-pairs.json') as f:
    data = json.load(f)
for entry in data.get('doctrine_entries', []):
    src = '$TEMPLATES_DIR/_shared/doctrine/' + entry['source_file']
    render_dir = entry['render_dir']
    print(f'doctrine_entry|{src}|{render_dir}')
" | while IFS='|' read -r _ src render_dir; do
  [[ -f "$src" ]] || { echo "  Missing doctrine source: $src"; continue; }
  dst_dir="$OUTPUT_DIR/$render_dir"
  mkdir -p "$dst_dir"
  substitute_placeholders "$src" "$dst_dir/$(basename "$src")"
done

echo "=== Mirroring Claude Agents/Commands to OpenCode ==="
python3 "$SCRIPT_DIR/generate-harness-mirrors.py" "$OUTPUT_DIR" "$TEMPLATES_DIR"

echo "=== Rendering Claude Code Harness ==="
render_harness "$TEMPLATES_DIR/claude-code/.claude" "$OUTPUT_DIR/.claude"
substitute_placeholders "$TEMPLATES_DIR/claude-code/CLAUDE.md" "$OUTPUT_DIR/CLAUDE.md"
substitute_placeholders "$TEMPLATES_DIR/_shared/AGENTS.md" "$OUTPUT_DIR/AGENTS.md"
python3 "$SCRIPT_DIR/generate-rule-index.py" "$OUTPUT_DIR"

echo "=== Rendering Opencode Harness ==="
render_harness "$TEMPLATES_DIR/opencode/.opencode" "$OUTPUT_DIR/.opencode"

echo "=== Rendering Shared Skills ==="
# Single source: templates/_shared/skills/<name>/ renders into every skill-aware
# harness (Claude Code + Opencode) so shipped skills never drift across platforms.
if [[ -d "$TEMPLATES_DIR/_shared/skills" ]]; then
  for skill_dir in "$TEMPLATES_DIR/_shared/skills"/*/; do
    [[ -d "$skill_dir" ]] || continue
    sname=$(basename "$skill_dir")
    for dest in ".claude/skills" ".opencode/skills"; do
      mkdir -p "$OUTPUT_DIR/$dest/$sname"
      while IFS= read -r src; do
        rel="${src#$skill_dir}"
        substitute_placeholders "$src" "$OUTPUT_DIR/$dest/$sname/$rel"
      done < <(find "$skill_dir" -name '__pycache__' -prune -o -type f -print | sort)
    done
  done
fi

if [[ -d "$TEMPLATES_DIR/_shared/profiles/$PROFILE/skills" ]]; then
  for skill_dir in "$TEMPLATES_DIR/_shared/profiles/$PROFILE/skills"/*/; do
    [[ -d "$skill_dir" ]] || continue
    sname=$(basename "$skill_dir")
    for dest in ".claude/skills" ".opencode/skills"; do
      mkdir -p "$OUTPUT_DIR/$dest/$sname"
      while IFS= read -r src; do
        rel="${src#$skill_dir}"
        substitute_placeholders "$src" "$OUTPUT_DIR/$dest/$sname/$rel"
      done < <(find "$skill_dir" -name '__pycache__' -prune -o -type f -print | sort)
    done
  done
fi

echo "=== Rendering Personal Workflow Profile ==="
# Ships an editable copy of the user's cross-project conventions into the project.
# customize-harness reads this on install and on every re-run.
if [[ -f "$TEMPLATES_DIR/_shared/my-workflows.md" ]]; then
  substitute_placeholders "$TEMPLATES_DIR/_shared/my-workflows.md" "$OUTPUT_DIR/my-workflows.md"
fi

echo "=== Rendering Harness Eval Prompt ==="
# Ships the harness-eval prompt into the target project so /harness-eval works.
mkdir -p "$OUTPUT_DIR/docs"
substitute_placeholders "$TEMPLATES_DIR/../docs/harness-eval.md" "$OUTPUT_DIR/docs/harness-eval.md" 2>/dev/null || \
  cp "$TEMPLATES_DIR/../docs/harness-eval.md" "$OUTPUT_DIR/docs/harness-eval.md" 2>/dev/null || \
  echo "  (harness-eval.md not found in genesis repo — skipping)"

echo "=== Rendering Git Hooks ==="
if [[ -d "$TEMPLATES_DIR/_shared/githooks" ]]; then
  mkdir -p "$OUTPUT_DIR/.githooks"
  for src in "$TEMPLATES_DIR/_shared/githooks/"*; do
    [[ -f "$src" ]] || continue
    dst="$OUTPUT_DIR/.githooks/$(basename "$src")"
    if [[ -e "$dst" && $FORCE_HOOKS -ne 1 ]]; then
      echo "  Skipped (existing): .githooks/$(basename "$src")"
      continue
    fi
    substitute_placeholders "$src" "$dst"
    chmod +x "$dst"
  done
  echo "  Git hooks rendered (use --force-hooks to replace existing ones)"
fi

echo "=== Rendering CI Workflow ==="
if [[ $WITH_CI -eq 1 && -f "$TEMPLATES_DIR/_shared/ci/$PROFILE.yml" ]]; then
  mkdir -p "$OUTPUT_DIR/.github/workflows"
  existing=$(find "$OUTPUT_DIR/.github/workflows" -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) | sed -n '1p')
  if [[ -n "$existing" && $FORCE_CI -ne 1 ]]; then
    echo "  Skipped (existing): ${existing#"$OUTPUT_DIR/"}"
  else
    substitute_placeholders "$TEMPLATES_DIR/_shared/ci/$PROFILE.yml" "$OUTPUT_DIR/.github/workflows/ci.yml"
    echo "  Wrote .github/workflows/ci.yml"
  fi
else
  echo "  Skipped (disabled or no template for profile: $PROFILE)"
fi

echo "=== Writing Harness Manifest ==="
python3 - "$OUTPUT_DIR" "$PROFILE" "$PROJECT_NAME" "$PROJECT_SLUG" \
  "$BACKEND_PATH" "$FRONTEND_PATH" "$PYTHON_VERSION" "$FASTAPI_VERSION" \
  "$REACT_VERSION" "$TYPESCRIPT_VERSION" "$VITE_VERSION" \
  "$PKG_MANAGER_BACKEND" "$PKG_MANAGER_FRONTEND" <<'PY'
import json
import sys
from pathlib import Path

out, profile, name, slug, backend, frontend, py, fastapi, react, ts, vite, pkg_b, pkg_f = sys.argv[1:]
manifest = {
    "schema": 1,
    "profile": profile,
    "project_name": name,
    "project_slug": slug,
    "backend_path": backend,
    "frontend_path": frontend,
    "python_version": py,
    "fastapi_version": fastapi,
    "react_version": react,
    "typescript_version": ts,
    "vite_version": vite,
    "package_manager_backend": pkg_b,
    "package_manager_frontend": pkg_f,
    "generated_by": "templates/scripts/bootstrap.sh",
}
path = Path(out) / ".claude" / "harness.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"  Wrote .claude/harness.json ({profile})")
PY

echo "=== Processing Conditional Blocks ==="
python3 "$SCRIPT_DIR/process-conditionals.py" "$OUTPUT_DIR" \
  "HAS_MLFLOW=$HAS_MLFLOW" \
  "HAS_LANGGRAPH=$HAS_LANGGRAPH" \
  "HAS_SUPABASE=$HAS_SUPABASE" \
  "HAS_POSTGRES=$HAS_POSTGRES" \
  "TAILWIND=$TAILWIND" \
  "ZOD_VALIDATION=$ZOD_VALIDATION" \
  "PROFILE_MCP=$([[ "$PROFILE" == "mcp" ]] && echo yes || echo no)" \
  "PROFILE_PYTHON=$([[ "$PROFILE" == "python" ]] && echo yes || echo no)" \
  "PROFILE_AGENT=$([[ "$PROFILE" == "agent" ]] && echo yes || echo no)" \
  "PROFILE_WEB=$([[ "$PROFILE" == "web" ]] && echo yes || echo no)" \
  "PROFILE_GODOT=$([[ "$PROFILE" == "godot" ]] && echo yes || echo no)"

echo ""
echo "=== Bootstrap Complete ==="
echo "Project: $PROJECT_NAME"
echo "Output:  $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $OUTPUT_DIR"
echo "  2. Review and customize rendered files"
echo "  3. Install git hooks: bash .claude/hooks/install-git-hooks.sh"
echo "  4. Run drift checker: python3 .claude/hooks/check-project-drift.py"
echo "  5. Commit the harness"
