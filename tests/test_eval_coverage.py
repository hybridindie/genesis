"""Every skill must have at least one behavioural case.

Coverage is the point of the eval suite: a skill without a case cannot be tuned,
because nothing states what its output must look like.
"""

from __future__ import annotations

import pytest

from conftest import ROOT

CASES = ROOT / "tests/evals/behaviour"


def skills() -> list[str]:
    names = {p.stem for p in (ROOT / ".agents/skills").glob("*.md")}
    names |= {p.parent.name for p in (ROOT / "templates/_shared").rglob("skills/*/SKILL.md")}
    return sorted(names)


@pytest.mark.parametrize("skill", skills())
def test_skill_has_a_behavioural_case(skill):
    cases = sorted((CASES / skill).glob("*.md"))
    assert cases, f"{skill} has no behavioural case in tests/evals/behaviour/{skill}/"


def test_the_skill_list_is_not_empty():
    assert len(skills()) >= 10
