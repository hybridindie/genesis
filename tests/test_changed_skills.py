"""The change detector decides which behavioural evals to run."""

from __future__ import annotations

from conftest import load

changed = load("scripts/changed-skills.py", "changed_skills")


def test_agent_skill_body_maps_to_its_name():
    assert changed.skill_from_path(".agents/skills/story-decomposer/SKILL.md") == "story-decomposer"
    assert changed.skill_from_path(".agents/skills/epic-composer/scripts/x.py") == "epic-composer"


def test_shipped_skill_body_maps_to_its_directory():
    assert changed.skill_from_path("templates/_shared/skills/ship-pr/SKILL.md") == "ship-pr"
    assert changed.skill_from_path("templates/_shared/stacks/fastapi/skills/create-migration/SKILL.md") == "create-migration"


def test_skill_scripts_count_as_a_skill_change():
    assert changed.skill_from_path("templates/_shared/skills/ship-pr/scripts/watch_pr.py") == "ship-pr"


def test_support_files_beside_a_skill_count_as_a_change():
    assert changed.skill_from_path(".agents/skills/epic-composer/references/rubric.md") == "epic-composer"
    assert changed.skill_from_path("templates/_shared/skills/ship-pr/assets/x.json") == "ship-pr"


def test_non_skill_paths_are_ignored():
    assert changed.skill_from_path("templates/_shared/core/articles/testing.md") is None
    assert changed.skill_from_path(".claude/skills/ship-pr/SKILL.md") is None
    assert changed.skill_from_path("docs/skill-evals.md") is None
