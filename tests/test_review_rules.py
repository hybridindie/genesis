"""The shipped .opencodereview/rule.json must stay consistent.

Two failure modes are silent:

- an `include` glob with no matching `rules` entry falls back to the default
  reviewer policy, so a file gets reviewed under different instructions
  depending on how it is named;
- OpenCodeReview expands only the **first** brace pair (expandBraces is not
  recursive), so `**/*.{test,spec}.{ts,js}` leaves a literal second pair that
  matches nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import ROOT

RULE_FILE = ROOT / "templates/_shared/.opencodereview/rule.json"


def expand(pattern: str) -> list[str]:
    """OCR's expandBraces: first brace pair only, no recursion."""
    start = pattern.find("{")
    if start < 0:
        return [pattern]
    end = pattern.find("}", start)
    if end < 0:
        return [pattern]
    return [pattern[:start] + option + pattern[end + 1:] for option in pattern[start + 1:end].split(",")]


def load() -> dict:
    return json.loads(RULE_FILE.read_text())


def covers(rule: str, included: str) -> bool:
    """Whether a rules glob subsumes an include glob.

    Identical globs match, and a rule ending in `/**` covers anything deeper
    under the same prefix (e.g. `**/.claude/**` covers `**/.claude/**/*.md`).
    """
    if rule == included:
        return True
    if rule.endswith("/**"):
        prefix = rule[:-3]
        return included.startswith(prefix + "/")
    return False


def test_every_included_glob_has_a_rule():
    data = load()
    rules = [p for rule in data["rules"] for p in expand(rule["path"])]
    missing = sorted(
        included
        for glob in data["include"]
        for included in expand(glob)
        if not any(covers(rule, included) for rule in rules)
    )
    assert not missing, f"included paths with no rules entry: {missing}"


def test_patterns_use_at_most_one_brace_pair():
    data = load()
    for pattern in data["include"] + [r["path"] for r in data["rules"]]:
        assert pattern.count("{") <= 1 and pattern.count("}") <= 1, (
            f"only the first brace pair expands, so a second one never matches: {pattern}"
        )


def test_no_duplicate_expanded_patterns():
    data = load()
    for field, patterns in (
        ("include", data["include"]),
        ("rules", [r["path"] for r in data["rules"]]),
    ):
        expanded = [p for pattern in patterns for p in expand(pattern)]
        duplicates = sorted({p for p in expanded if expanded.count(p) > 1})
        assert not duplicates, f"{field} repeats a pattern after expansion: {duplicates}"
