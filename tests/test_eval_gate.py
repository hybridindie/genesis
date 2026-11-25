"""The regression gate around `claude plugin eval`, and the fixture graders it relies on.

No model calls: the gate is tested on a synthetic aggregate-result.json, and
every grader file is linted against the documented frontmatter schema so a
typo fails here instead of after a paid run.
"""

from __future__ import annotations

import json
import re

import pytest
import yaml

from conftest import ROOT, load

gate = load("scripts/eval-gate.py", "eval_gate")
CASES = ROOT / ".agents/evals/cases"
GRADERS = sorted(CASES.glob("*/graders/*.md"))

# https://code.claude.com/docs/en/plugin-evals.md#grader-frontmatter
COMMON = {"type", "weight", "arm"}
KEYS = {
    "regex": {"pattern", "flags", "match", "target"},
    "tool_used": {"tool", "input_match", "min", "max"},
    "tool_order": {"before", "after"},
    "file_exists": {"path", "exists"},
    "llm": {"criteria", "focus"},
    "baseline": {"baseline_file", "criteria"},
}
TARGETS = {"last_message", "trace", "files", "mock_calls"}


def frontmatter(path):
    _, front, body = path.read_text(encoding="utf-8").split("---", 2)
    return yaml.safe_load(front), body.strip()


def result(**scores):
    return {"schemaVersion": 1, "partial": False,
            "aggregates": {"overallScore": 0.5, "casesPassed": 0, "casesTotal": len(scores)},
            "cases": [{"name": n, "aggregates": {"score": s}} for n, s in scores.items()],
            "costUsd": 1.25, "durationSeconds": 60, "claudeVersion": "2.1.332"}


def test_scores_come_from_documented_fields():
    assert gate.case_scores(result(a=0.8, b=1.0)) == {"a": 0.8, "b": 1.0}


def test_a_drop_beyond_tolerance_fails():
    base = {"cases": {"a": {"score": 0.9}, "b": {"score": 0.9}}}
    v = gate.gate({"a": 0.8, "b": 0.7}, base, ["a", "b"], tolerance=0.15, strict=False)
    assert [x.status for x in v] == ["pass", "regressed"]
    assert v[1].delta == pytest.approx(-0.2)
    assert gate.failed(v)


def test_a_case_without_baseline_is_reported_unless_strict():
    v = gate.gate({"a": 0.2}, {"cases": {}}, ["a"], 0.15, strict=False)
    assert v[0].status == "no-baseline" and not gate.failed(v)
    assert gate.failed(gate.gate({"a": 0.2}, {"cases": {}}, ["a"], 0.15, strict=True))


def test_a_selected_case_missing_from_the_result_fails():
    v = gate.gate({}, {"cases": {"a": {"score": 1.0}}}, ["a"], 0.15, False)
    assert v[0].status == "missing" and gate.failed(v)


def test_an_errored_run_fails_even_without_a_baseline():
    # Seen for real: a missing sandbox refused every run, and the gate printed PASS.
    res = result(a=0.125)
    res["cases"][0]["arms"] = {"with": [{"score": 0.125, "error": "exit 1: Sandbox required but unavailable"}]}
    errors = gate.errored_cases(res)
    assert errors == {"a": "exit 1: Sandbox required but unavailable"}
    v = gate.gate(gate.case_scores(res), {"cases": {}}, ["a"], 0.15, strict=False, errors=errors)
    assert v[0].status == "errored" and gate.failed(v)


def test_update_baseline_keeps_other_cases(tmp_path):
    out = gate.update_baseline({"cases": {"old": {"score": 1.0}}}, {"new": 0.66666}, {"runs": 3})
    assert out["cases"] == {"new": {"score": 0.6667, "runs": 3}, "old": {"score": 1.0}}


def test_cli_gates_an_existing_result(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVAL_GATE_NO_MLFLOW", "1")
    case = sorted(gate.case_skills())[0]
    res = tmp_path / "r.json"
    res.write_text(json.dumps(result(**{case: 0.1})))
    base = tmp_path / "b.json"
    base.write_text(json.dumps({"cases": {case: {"score": 1.0}}}))
    assert gate.main(["--result", str(res), "--baseline", str(base), "--skill", gate.case_skills()[case][0]]) == 1
    assert "regressed" in capsys.readouterr().out


def test_cli_refuses_a_baseline_from_errored_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("EVAL_GATE_NO_MLFLOW", "1")
    case = sorted(gate.case_skills())[0]
    res = result(**{case: 0.0})
    res["cases"][0]["arms"] = {"with": [{"score": 0, "error": "timed out after 900s"}]}
    path = tmp_path / "r.json"
    path.write_text(json.dumps(res))
    base = tmp_path / "b.json"
    assert gate.main(["--result", str(path), "--baseline", str(base), "--skill",
                      gate.case_skills()[case][0], "--update-baseline"]) == 2
    assert not base.exists()


def test_cli_refuses_to_gate_a_partial_result(tmp_path, monkeypatch):
    monkeypatch.setenv("EVAL_GATE_NO_MLFLOW", "1")
    res = tmp_path / "r.json"
    res.write_text(json.dumps({**result(), "partial": True, "partialReason": "cost_ceiling"}))
    assert gate.main(["--result", str(res), "--all"]) == 2


def test_committed_baseline_is_valid_json_with_known_cases():
    data = json.loads((ROOT / ".agents/evals/baseline.json").read_text())
    assert set(data["cases"]) <= set(gate.case_skills())


@pytest.mark.parametrize("case", sorted(gate.case_skills()))
def test_every_fixture_case_names_a_real_skill(case):
    skills = gate.case_skills()[case]
    assert skills, f"{case}/prompt.md needs a skill:<name> tag so the gate can select it"
    for skill in skills:
        assert (ROOT / ".agents/skills" / skill / "SKILL.md").exists(), f"{case}: no skill {skill}"


@pytest.mark.parametrize("case", sorted(gate.case_skills()))
def test_every_fixture_case_checks_that_its_skill_fired(case):
    fired = [frontmatter(g)[0] for g in (CASES / case / "graders").glob("*.md")]
    assert any(f["type"] == "tool_used" and f.get("tool") == "Skill" and f.get("arm") == "with-only"
               for f in fired), f"{case} has no with-only Skill indicator"


@pytest.mark.parametrize("grader", GRADERS, ids=lambda p: f"{p.parent.parent.name}/{p.stem}")
def test_grader_frontmatter_matches_the_schema(grader):
    front, body = frontmatter(grader)
    kind = front.get("type")
    assert kind in KEYS, f"unknown grader type {kind!r}"
    unknown = set(front) - COMMON - KEYS[kind]
    assert not unknown, f"unknown keys {sorted(unknown)}"
    assert body, "a grader needs a body: the criteria (llm) or a statement of what it checks"
    where = front.get("target" if kind == "regex" else "focus")
    if isinstance(where, dict):
        assert where.get("source") == "file" and where.get("path"), where
    elif where is not None:
        assert where in TARGETS, where
    if kind == "regex":
        re.compile(front["pattern"])  # JS and Python agree on the subset used here
        match = front.get("match")
        assert match in (None, "contains", "not_contains") or re.fullmatch(r"count:\d+", str(match)), match
    if kind == "tool_used" and "input_match" in front:
        re.compile(front["input_match"])


def test_deterministic_checks_do_not_use_a_judge():
    """Facts a regex or tool count can settle must not cost a judge call or vary between votes."""
    llm = [g for g in GRADERS if frontmatter(g)[0]["type"] == "llm"]
    phrases = re.compile(r"exactly one fenced|passes `?plan\.py validate|file exists for each|"
                         r"no branches or worktrees were created", re.I)
    offenders = [f"{g.parent.parent.name}/{g.stem}" for g in llm if phrases.search(frontmatter(g)[1])]
    assert not offenders, offenders


def test_deterministic_patterns_match_what_plan_py_prints():
    import subprocess, sys
    out = subprocess.run([sys.executable, str(ROOT / ".agents/scripts/plan.py"), "validate",
                          str(ROOT / "tests/evals/epic.md"), str(ROOT / "tests/evals/story.md")],
                         capture_output=True, text=True).stdout
    assert re.search(r"PASS: epic \+ 1 stories", out), out


def test_the_skills_are_packaged_as_a_plugin():
    """Without the manifest, `claude plugin eval .agents` loads no skills and every case measures bare Claude."""
    manifest = json.loads((ROOT / ".agents/.claude-plugin/plugin.json").read_text())
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", manifest["name"])
