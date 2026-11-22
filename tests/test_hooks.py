"""The gates must fail on the defect and pass on the fix.

Each case pins a blind spot found by review: shape normalisation and the
read-action requirement in the drift hook, `.skip.each` and missing roots in
the skip gate, dotenv literals inside code, and frontmatter-less mirror pairs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import ROOT, load

drift = load("templates/claude-code/.claude/hooks/check-project-drift.py", "drift")
secrets = load("templates/claude-code/.claude/hooks/check-secrets.py", "secrets")
render = load("templates/scripts/render.py", "render")

HOOKS = ROOT / "templates/claude-code/.claude/hooks"


# ── check-project-drift ───────────────────────────────────────────────────


def test_string_instructions_are_not_split_into_characters():
    assert drift.Drift.path_list(".opencode/skills") == [".opencode/skills"]


def test_skills_object_and_list_forms():
    assert drift.Drift.path_list([".opencode/skills"]) == [".opencode/skills"]
    assert drift.Drift.path_list({"paths": [".opencode/skills"]}) == [".opencode/skills"]
    assert drift.Drift.path_list(None) == []


def test_only_a_read_deny_counts_as_protecting_env():
    write_only = {"permissions": [{"action": "edit", "resource": ".env", "effect": "deny"}]}
    read_deny = {"permissions": [{"action": "read", "resource": "**/.env", "effect": "deny"}]}
    legacy = {"permission": {".env": "deny"}}
    assert drift.Drift.denies_env(write_only) is False
    assert drift.Drift.denies_env(read_deny) is True
    assert drift.Drift.denies_env(legacy) is True


def test_a_globbed_env_deny_counts():
    # OpenCode's `permission.read` takes globs: "*.env" denies every .env.
    assert drift.Drift.is_env_path("*.env") is True
    assert drift.Drift.is_env_path("*.env.*") is True
    assert drift.Drift.is_env_path("*.env.example") is False
    assert drift.Drift.denies_env({"read": {"*": "allow", "*.env": "deny"}}) is True


def test_rule_aliases_name_a_tailored_stack_rule(tmp_path):
    rules = tmp_path / ".claude/rules"
    rules.mkdir(parents=True)
    (rules / "native.md").write_text("---\nread_when: x\n---\n")
    plain = drift.Drift(tmp_path)
    plain.stacks({"stacks": ["rust"]})
    assert any("stack rust has no" in w for w in plain.warnings)
    aliased = drift.Drift(tmp_path)
    aliased.stacks({"stacks": ["rust"], "rule_aliases": {"rust": "native.md"}})
    assert not any("stack rust" in w for w in aliased.warnings)
    assert not aliased.errors


def test_a_dangling_skill_link_is_still_a_skill(tmp_path):
    # A skill linked to a sibling checkout dangles where the checkout is absent
    # (CI): it is still listed, not reported missing.
    (tmp_path / ".claude/skills").mkdir(parents=True)
    (tmp_path / ".claude/skills/linked").symlink_to(tmp_path / "absent/linked")
    (tmp_path / "AGENTS.md").write_text("### Commands\n\n### Skills\n\n`linked`\n")
    checker = drift.Drift(tmp_path)
    checker.map_lists()
    assert not any("linked" in e for e in checker.errors)


def test_env_template_files_do_not_count():
    assert drift.Drift.is_env_path("**/.env") is True
    assert drift.Drift.is_env_path(".env.example") is False
    assert drift.Drift.is_env_path("environments/prod") is False


# ── check-secrets ─────────────────────────────────────────────────────────


def test_bare_literal_in_a_code_string_is_reported():
    findings: list[str] = []
    line = 'doc = """\nMY_TOKEN=abcdefghijklmnop1234\n"""'
    secrets.scan_text(line, "src/app.py", findings)
    assert findings, "a bare dotenv literal inside code must still be reported"


def test_environment_lookup_in_code_is_not_a_secret():
    findings: list[str] = []
    secrets.scan_text("MY_TOKEN=os.environ['MY_TOKEN']", "src/app.py", findings)
    assert findings == []


# ── check-primitive-drift ─────────────────────────────────────────────────


def run_script(script: Path, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(script)], cwd=cwd, capture_output=True, text=True)


def test_frontmatterless_pair_with_different_bodies_is_drift(tmp_path):
    for base, body in ((".claude", "one\n"), (".opencode", "two\n")):
        d = tmp_path / base / "commands"
        d.mkdir(parents=True)
        (d / "demo.md").write_text(body)
    result = run_script(HOOKS / "check-primitive-drift.sh", tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr


def test_frontmatterless_pair_with_equal_bodies_passes(tmp_path):
    for base in (".claude", ".opencode"):
        d = tmp_path / base / "commands"
        d.mkdir(parents=True)
        (d / "demo.md").write_text("same body\n")
    result = run_script(HOOKS / "check-primitive-drift.sh", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


# ── check-no-skipped-tests ────────────────────────────────────────────────


def render_skip_gate(tmp_path: Path, flags: dict[str, bool]) -> Path:
    source = (HOOKS / "check-no-skipped-tests.sh").read_text()
    values = {"BACKEND_PATH": ".", "FRONTEND_PATH": "frontend", "GODOT_PATH": ".", "RUST_PATH": "."}
    all_flags = {"STACK_PYTHON": False, "STACK_FRONTEND": False, "STACK_GODOT": False, "STACK_RUST": False}
    all_flags.update(flags)  # unknown flags leave their block intact
    script = tmp_path / "skip-gate.sh"
    script.write_text(render.render_text(source, values, all_flags))
    return script


def test_skip_each_is_reported(tmp_path):
    (tmp_path / "frontend" / "src").mkdir(parents=True)
    (tmp_path / "frontend" / "src" / "a.test.ts").write_text("it.skip.each([1])('x', () => {})\n")
    script = render_skip_gate(tmp_path, {"STACK_FRONTEND": True})
    result = run_script(script, tmp_path)
    assert result.returncode == 1
    assert "a.test.ts" in result.stdout


def test_missing_root_is_reported_not_silently_passed(tmp_path):
    (tmp_path / "frontend" / "src").mkdir(parents=True)
    (tmp_path / "frontend" / "src" / "a.test.ts").write_text("it('x', () => {})\n")
    script = render_skip_gate(tmp_path, {"STACK_FRONTEND": True})
    result = run_script(script, tmp_path)
    assert result.returncode == 0
    assert "no such test root" in result.stderr
    assert "frontend/e2e" in result.stderr


def _skill_tree(root, pointer_text):
    body = root / ".agents/skills/a/SKILL.md"
    body.parent.mkdir(parents=True)
    body.write_text("---\nname: a\n---\n")
    extra = root / ".claude/skills/old/SKILL.md"
    extra.parent.mkdir(parents=True)
    extra.write_text(pointer_text)
    (root / ".claude/skills/a").mkdir(parents=True)
    (root / ".claude/skills/a/SKILL.md").write_text(
        "<!-- generated by scripts/sync-skill-wrappers.py from .agents/skills/a/SKILL.md -->\n")


def test_drift_warns_on_a_skill_copy_that_is_not_a_generated_pointer(tmp_path):
    _skill_tree(tmp_path, "---\nname: old\n---\n# a full, stale copy of a skill\n")
    checker = drift.Drift(tmp_path)
    checker.mirrors()
    assert any(".claude/skills/old" in w for w in checker.warnings)
    assert not any(".claude/skills/old" in e for e in checker.errors)


def test_drift_fails_a_generated_pointer_whose_skill_is_gone(tmp_path):
    _skill_tree(tmp_path, "<!-- generated by scripts/sync-skill-wrappers.py from "
                          ".agents/skills/old/SKILL.md -->\nRead .agents/skills/old/SKILL.md\n")
    checker = drift.Drift(tmp_path)
    checker.mirrors()
    assert any(".claude/skills/old" in e for e in checker.errors)
