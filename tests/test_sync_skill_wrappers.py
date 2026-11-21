"""The generated .claude/skills pointers: written, checked, and cleaned up."""

from __future__ import annotations

from conftest import load

sync = load("scripts/sync-skill-wrappers.py", "sync_skill_wrappers")

BODY = "---\nname: {n}\ndescription: does {n}\n---\n\n# {n}\n"


def skill(root, name, text=None):
    p = root / ".agents" / "skills" / name / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text if text is not None else BODY.format(n=name))


def pointer_path(root, name):
    return root / ".claude" / "skills" / name / "SKILL.md"


def test_writes_a_pointer_per_skill(tmp_path):
    skill(tmp_path, "a")
    result = sync.sync(tmp_path, check=False)
    assert result["ok"] and result["updated"] == [".claude/skills/a/SKILL.md"]
    assert ".agents/skills/a/SKILL.md" in pointer_path(tmp_path, "a").read_text()


def test_check_reports_and_write_removes_an_orphaned_pointer(tmp_path):
    skill(tmp_path, "a")
    skill(tmp_path, "gone")
    sync.sync(tmp_path, check=False)
    (tmp_path / ".agents/skills/gone/SKILL.md").unlink()
    checked = sync.sync(tmp_path, check=True)
    assert not checked["ok"] and checked["orphaned"] == [".claude/skills/gone/SKILL.md"]
    assert pointer_path(tmp_path, "gone").exists()          # --check writes nothing
    sync.sync(tmp_path, check=False)
    assert not pointer_path(tmp_path, "gone").exists()


def test_leaves_a_hand_written_wrapper_alone(tmp_path):
    skill(tmp_path, "a")
    hand = pointer_path(tmp_path, "ship-pr")
    hand.parent.mkdir(parents=True)
    hand.write_text("---\nname: ship-pr\n---\nRead templates/_shared/skills/ship-pr/SKILL.md\n")
    assert sync.sync(tmp_path, check=True)["orphaned"] == []


def test_broken_frontmatter_fails_cleanly_and_writes_nothing(tmp_path):
    skill(tmp_path, "a")
    skill(tmp_path, "b", text="no frontmatter here\n")
    result = sync.sync(tmp_path, check=False)
    assert not result["ok"] and "missing frontmatter" in result["errors"][0]
    assert not pointer_path(tmp_path, "a").exists()          # validate first, then write
