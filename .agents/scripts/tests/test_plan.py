"""Calibration tests for plan.py: is each rule as strict as it should be?

Two families, named so a failure says which way the rule is wrong:

- `test_accepts_*`  a plan a careful planner would write must PASS.
  A failure means the rule is too strict (it would push planners to
  serialize work or invent structure for no benefit).
- `test_rejects_*`  a plan that would cause a collision, an untraceable unit
  or a stuck schedule must FAIL. A failure means the rule is too relaxed.

Scheduling (`next`), briefs and the dispatch-time scope check get the same
treatment. Run:

  uv run --with pytest --with pyyaml pytest .agents/scripts/tests -q
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("plan", HERE.parent / "plan.py")
plan = importlib.util.module_from_spec(spec)
sys.modules["plan"] = plan
spec.loader.exec_module(plan)


# ── builders ─────────────────────────────────────────────────────────────────

def epic(stories, acs=("AC1", "AC2", "AC3"), contracts=()):
    return {"version": 1, "kind": "epic", "acs": list(acs), "contracts": list(contracts),
            "stories": stories}


def estory(sid, owns, acs=("AC1",), depends_on=(), **kw):
    return {"id": sid, "title": f"story {sid}", "size": "S", "acs": list(acs),
            "owns": list(owns), "depends_on": list(depends_on), "verify": "make test", **kw}


def track(tid, owns, depends_on=(), kind="track", **kw):
    return {"id": tid, "kind": kind, "owns": list(owns), "depends_on": list(depends_on),
            "verify": f"make test-{tid}", **kw}


def story(sid, owns, tracks, acs=("AC1",), tasks=None, integration=None, **kw):
    s = {"version": 1, "kind": "story", "story": sid, "acs": list(acs), "owns": list(owns),
         "verify": "make test", "tracks": tracks}
    if tasks is not None:
        s["tasks"] = tasks
    if integration is not None:
        s["integration"] = integration
    s.update(kw)
    return s


def task(kid, trk, files, acs=("AC1",), **kw):
    return {"id": kid, "track": trk, "do": f"do {kid}", "files": list(files),
            "verify": "make test", "acs": list(acs), **kw}


def three_story_epic():
    return epic([
        estory("S1", ["backend/**"], acs=["AC1"]),
        estory("S2", ["frontend/**"], acs=["AC2"]),
        estory("S3", ["docs/**"], acs=["AC3"], depends_on=["S1", "S2"]),
    ])


def errors_epic(e):
    return plan.validate_epic(e)


def errors_story(s):
    return plan.validate_story(s)


# ── epic: too strict? ────────────────────────────────────────────────────────

def test_accepts_contract_first_epic_with_one_story_in_wave_1():
    e = epic([
        estory("S1", ["shared/types.py"], acs=["AC1"]),
        estory("S2", ["backend/**"], acs=["AC2"], depends_on=["S1"]),
        estory("S3", ["frontend/**"], acs=["AC3"], depends_on=["S1"]),
    ], contracts=[{"id": "C1", "what": "types", "owner": "S1", "paths": ["shared/types.py"]}])
    assert errors_epic(e) == []


def test_accepts_sequential_epic_when_work_is_genuinely_ordered():
    e = epic([
        estory("S1", ["db/migrations/**"], acs=["AC1"]),
        estory("S2", ["jobs/backfill.py"], acs=["AC2"], depends_on=["S1"]),
        estory("S3", ["api/**"], acs=["AC3"], depends_on=["S2"]),
    ])
    assert errors_epic(e) == []


def test_accepts_dependent_stories_that_touch_the_same_file():
    # Ordered by depends_on, so they never run at the same time.
    e = epic([
        estory("S1", ["app/main.py", "app/a/**"], acs=["AC1", "AC2"]),
        estory("S2", ["app/main.py", "app/b/**"], acs=["AC3"], depends_on=["S1"]),
    ])
    assert errors_epic(e) == []


def test_accepts_sibling_files_in_the_same_directory():
    e = epic([
        estory("S1", ["app/reports/pdf.py"], acs=["AC1"]),
        estory("S2", ["app/reports/csv.py"], acs=["AC2"]),
        estory("S3", ["app/reports/xlsx.py"], acs=["AC3"]),
    ])
    assert errors_epic(e) == []


def test_accepts_similarly_named_directories():
    e = epic([
        estory("S1", ["src/api/**"], acs=["AC1"]),
        estory("S2", ["src/api_v2/**"], acs=["AC2"]),
        estory("S3", ["src/apis.md"], acs=["AC3"]),
    ])
    assert errors_epic(e) == []


def test_accepts_one_level_glob_next_to_a_subdirectory():
    # `src/*.py` matches files directly in src/, never src/api/x.py.
    e = epic([
        estory("S1", ["src/*.py"], acs=["AC1"]),
        estory("S2", ["src/api/**"], acs=["AC2"]),
        estory("S3", ["docs/**"], acs=["AC3"]),
    ])
    assert errors_epic(e) == []


def test_accepts_enabling_story_traced_to_a_constraint():
    e = epic([
        estory("S1", ["infra/**"], acs=[], constraint="Reuse the existing cron container"),
        estory("S2", ["backend/**"], acs=["AC1", "AC2", "AC3"], depends_on=["S1"]),
    ])
    assert errors_epic(e) == []


def test_accepts_an_ac_covered_by_two_stories():
    # Backend and UI halves of one criterion is normal.
    e = epic([
        estory("S1", ["backend/**"], acs=["AC1", "AC2"]),
        estory("S2", ["frontend/**"], acs=["AC1", "AC3"]),
    ])
    assert errors_epic(e) == []


# ── epic: too relaxed? ───────────────────────────────────────────────────────

def test_rejects_parallel_stories_owning_the_same_file():
    e = three_story_epic()
    e["stories"][1]["owns"].append("backend/app/main.py")
    assert any("can run in parallel" in x for x in errors_epic(e))


def test_rejects_parallel_stories_where_a_tree_contains_the_other_file():
    e = epic([
        estory("S1", ["frontend/src/**"], acs=["AC1"]),
        estory("S2", ["frontend/src/api.ts"], acs=["AC2"]),
        estory("S3", ["docs/**"], acs=["AC3"]),
    ])
    assert any("can run in parallel" in x for x in errors_epic(e))


def test_rejects_parallel_stories_transitively_unordered():
    # S2 and S3 both depend on S1 but not on each other -> they run together.
    e = epic([
        estory("S1", ["a/**"], acs=["AC1"]),
        estory("S2", ["lib/x.py"], acs=["AC2"], depends_on=["S1"]),
        estory("S3", ["lib/x.py"], acs=["AC3"], depends_on=["S1"]),
    ])
    assert any("S2 and S3" in x for x in errors_epic(e))


def test_rejects_a_dependency_cycle():
    e = three_story_epic()
    e["stories"][0]["depends_on"] = ["S3"]
    assert any("cycle" in x for x in errors_epic(e))


def test_rejects_an_ac_no_story_covers():
    e = three_story_epic()
    e["acs"].append("AC4")
    assert any("acs with no story" in x for x in errors_epic(e))


def test_rejects_a_story_without_verify():
    e = three_story_epic()
    del e["stories"][0]["verify"]
    assert any("missing verify" in x for x in errors_epic(e))


def test_rejects_too_many_acs():
    e = three_story_epic()
    e["acs"] = [f"AC{i}" for i in range(1, 10)]
    assert any("3-8" in x for x in errors_epic(e))


def test_rejects_a_blank_verify_command():
    e = three_story_epic()
    e["stories"][0]["verify"] = "   "
    assert any("verify" in x for x in errors_epic(e))


def test_rejects_a_placeholder_verify_command():
    # Template placeholders left in a plan look like a command but aren't one.
    e = three_story_epic()
    e["stories"][0]["verify"] = "<command>"
    assert any("verify" in x for x in errors_epic(e))


def test_accepts_verify_baseline_pass_on_a_refactor_track():
    s = story("S1", ["a/**"], [track("main", ["a/**"], verify_baseline="pass")])
    assert not [x for x in plan.validate_story(s) if "verify_baseline" in x]


def test_rejects_an_unknown_verify_baseline():
    s = story("S1", ["a/**"], [track("main", ["a/**"], verify_baseline="green")])
    assert any("verify_baseline" in x for x in plan.validate_story(s))


def test_rejects_ownership_of_the_whole_repo_alongside_parallel_work():
    e = three_story_epic()
    e["stories"][0]["owns"] = ["**"]
    assert any("can run in parallel" in x for x in errors_epic(e))


def test_rejects_parallel_stories_both_owning_a_lockfile():
    e = epic([
        estory("S1", ["backend/app/a.py", "backend/uv.lock"], acs=["AC1"]),
        estory("S2", ["backend/app/b.py", "backend/uv.lock"], acs=["AC2"]),
        estory("S3", ["docs/**"], acs=["AC3"]),
    ])
    assert any("uv.lock" in x for x in errors_epic(e))


# ── story: too strict? ───────────────────────────────────────────────────────

def test_accepts_a_single_track_story():
    s = story("S1", ["app/**"], [track("main", ["app/**"])])
    assert errors_story(s) == []


def test_accepts_contract_then_two_parallel_tracks():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/api.py"], ["contract"]),
        track("B", ["app/ui.py"], ["contract"]),
    ], integration={"merge_order": ["contract", "A", "B"], "verify": "make e2e"})
    assert errors_story(s) == []


def test_accepts_a_track_that_depends_on_the_contract_through_another_track():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
        track("A2", ["app/a2.py"], ["A"]),
    ], integration={"merge_order": ["contract", "A", "A2"], "verify": "make e2e"})
    assert errors_story(s) == []


def test_accepts_a_task_file_under_a_directory_the_track_owns_without_a_glob():
    s = story("S1", ["app/**"], [track("main", ["app/reports/"])],
              tasks=[task("T1", "main", ["app/reports/pdf.py"])])
    assert errors_story(s) == []


def test_accepts_a_directory_owned_without_trailing_slash_or_glob():
    s = story("S1", ["app/**"], [track("main", ["app/reports"])],
              tasks=[task("T1", "main", ["app/reports/pdf.py"])])
    assert errors_story(s) == []


def test_accepts_a_prerequisite_task_with_no_ac():
    s = story("S1", ["app/**"], [track("main", ["app/**"])],
              tasks=[task("T1", "main", ["app/x.py"], acs=[]),
                     task("T2", "main", ["app/y.py"], depends_on=["T1"])])
    assert errors_story(s) == []


def test_accepts_tracks_without_tasks():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
    ], integration={"merge_order": ["contract", "A"], "verify": "make e2e"})
    assert errors_story(s) == []


# ── story: too relaxed? ──────────────────────────────────────────────────────

def test_rejects_parallel_tracks_owning_the_same_file():
    s = story("S1", ["app/**"], [
        track("A", ["app/main.py", "app/a.py"]),
        track("B", ["app/main.py", "app/b.py"]),
    ], integration={"merge_order": ["A", "B"], "verify": "make e2e"})
    assert any("can run in parallel" in x for x in errors_story(s))


def test_rejects_a_track_owning_paths_outside_its_story():
    s = story("S1", ["backend/**"], [track("main", ["frontend/x.ts"])])
    assert any("outside the story" in x for x in errors_story(s))


def test_rejects_a_track_broader_than_its_story():
    # The story owns one file; the track claims the whole tree around it.
    s = story("S1", ["backend/app/reports/pdf.py"], [track("main", ["backend/**"])])
    assert any("outside the story" in x for x in errors_story(s))


def test_rejects_a_task_file_outside_its_track():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
    ], tasks=[task("T1", "A", ["app/types.py"])],
        integration={"merge_order": ["contract", "A"], "verify": "make e2e"})
    assert any("outside track A" in x for x in errors_story(s))


def test_rejects_a_track_that_skips_the_contract():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"]),
    ], integration={"merge_order": ["contract", "A"], "verify": "make e2e"})
    assert any("does not depend on the contract" in x for x in errors_story(s))


def test_rejects_multiple_tracks_without_integration_verify():
    s = story("S1", ["app/**"], [track("A", ["app/a.py"]), track("B", ["app/b.py"])])
    assert any("integration.verify" in x for x in errors_story(s))


def test_rejects_a_story_ac_no_task_covers():
    s = story("S1", ["app/**"], [track("main", ["app/**"])], acs=["AC1", "AC2"],
              tasks=[task("T1", "main", ["app/x.py"], acs=["AC1"])])
    assert any("acs with no task" in x for x in errors_story(s))


def test_rejects_a_task_depending_on_an_unknown_task():
    s = story("S1", ["app/**"], [track("main", ["app/**"])],
              tasks=[task("T1", "main", ["app/x.py"], depends_on=["T9"])])
    assert any("T9" in x for x in errors_story(s))


def test_rejects_a_task_depending_on_a_task_in_a_parallel_track():
    # A's task cannot wait on B's task when A and B run at the same time.
    s = story("S1", ["app/**"], [track("A", ["app/a.py"]), track("B", ["app/b.py"])],
              tasks=[task("T1", "A", ["app/a.py"]), task("T2", "B", ["app/b.py"], depends_on=["T1"])],
              integration={"merge_order": ["A", "B"], "verify": "make e2e"})
    assert any("T1" in x for x in errors_story(s))


def test_rejects_merge_order_that_merges_a_track_before_its_dependency():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
    ], integration={"merge_order": ["A", "contract"], "verify": "make e2e"})
    assert any("merge_order" in x for x in errors_story(s))


# ── scheduling ───────────────────────────────────────────────────────────────

def stories_for(e):
    return [
        story("S1", ["backend/**"], [track("main", ["backend/**"])]),
        story("S2", ["frontend/**"], [track("main", ["frontend/**"])], acs=["AC2"]),
        story("S3", ["docs/**"], [track("main", ["docs/**"])], acs=["AC3"], depends_on=["S1", "S2"]),
    ]


def units_of(runnable):
    return [u["unit"] for u in runnable]


def test_next_starts_every_independent_track():
    e = three_story_epic()
    assert units_of(plan.next_runnable(e, stories_for(e), 9)) == ["S1/main", "S2/main"]


def test_next_respects_the_concurrency_limit():
    e = three_story_epic()
    assert len(plan.next_runnable(e, stories_for(e), 1)) == 1


def test_next_waits_for_upstream_stories():
    e = three_story_epic()
    ss = stories_for(e)
    ss[0]["tracks"][0]["status"] = "done"
    assert "S3/main" not in units_of(plan.next_runnable(e, ss, 9))
    ss[1]["tracks"][0]["status"] = "done"
    assert units_of(plan.next_runnable(e, ss, 9)) == ["S3/main"]


def test_next_blocks_dependants_of_an_unplanned_story():
    e = three_story_epic()
    ss = [stories_for(e)[0], stories_for(e)[2]]  # S2 has no story plan yet
    ss[0]["tracks"][0]["status"] = "done"
    assert units_of(plan.next_runnable(e, ss, 9)) == []


def test_next_does_not_restart_running_or_blocked_tracks():
    e = three_story_epic()
    ss = stories_for(e)
    ss[0]["tracks"][0]["status"] = "running"
    ss[1]["tracks"][0]["status"] = "blocked"
    assert units_of(plan.next_runnable(e, ss, 9)) == []


def test_next_starts_a_contract_before_its_tracks():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
    ], integration={"merge_order": ["contract", "A"], "verify": "make e2e"})
    assert units_of(plan.next_runnable(None, [s], 9)) == ["S1/contract"]


def test_next_holds_back_a_track_that_overlaps_a_running_one():
    # Two stories that the epic orders, but whose plans drifted to overlap:
    # never run the second while the first is running.
    a = story("S1", ["app/**"], [track("main", ["app/shared.py"], status="running")])
    b = story("S2", ["app/**"], [track("main", ["app/shared.py"])], acs=["AC2"])
    assert units_of(plan.next_runnable(None, [a, b], 9)) == []


# ── briefs ───────────────────────────────────────────────────────────────────

def test_brief_includes_the_acs_when_the_track_has_no_tasks():
    s = story("S1", ["app/**"], [track("main", ["app/**"])], acs=["AC1"],
              ac_text={"AC1": "Given a report, when exported, then a PDF downloads."})
    assert "then a PDF downloads" in plan.brief(s, "main")


def test_brief_lists_paths_owned_by_sibling_tracks_as_off_limits():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract"),
        track("A", ["app/a.py"], ["contract"]),
        track("B", ["app/b.py"], ["contract"]),
    ], integration={"merge_order": ["contract", "A", "B"], "verify": "make e2e"})
    text = plan.brief(s, "A")
    assert "`app/b.py`" in text.split("Do not change:")[1].splitlines()[0]


def test_brief_uses_track_context_instead_of_story_context():
    s = story("S1", ["app/**"], [
        track("contract", ["app/types.py"], kind="contract", context="Only define the types."),
        track("A", ["app/a.py"], ["contract"]),
    ], context="Also mount the router in app/main.py.",
        integration={"merge_order": ["contract", "A"], "verify": "make e2e"})
    text = plan.brief(s, "contract")
    assert "Only define the types." in text
    assert "app/main.py" not in text


# ── dispatch-time scope check ────────────────────────────────────────────────

def owns_ok(path, owns):
    return plan.covered_by(path, owns)


@pytest.mark.parametrize("path,owns,expected", [
    ("app/reports/pdf.py", ["app/reports/**"], True),
    ("app/reports/pdf.py", ["app/reports/pdf.py"], True),
    ("app/reports/pdf.py", ["app/reports/"], True),
    ("app/reports/pdf.py", ["app/reports"], True),       # directory named without slash
    ("app/reports/sub/x.py", ["app/reports/*.py"], False),  # one-level glob
    ("app/reports/x.py", ["app/reports/*.py"], True),
    ("app/reports_v2/x.py", ["app/reports/**"], False),
    ("app/other.py", ["app/reports/**"], False),
    ("./app/reports/pdf.py", ["app/reports/**"], True),  # git may print ./-prefixed paths
])
def test_scope_matches_paths_the_way_owners_mean_them(path, owns, expected):
    assert owns_ok(path, owns) is expected


# ── extraction ───────────────────────────────────────────────────────────────

def test_extract_rejects_two_plan_blocks():
    text = "```yaml agent-plan\nversion: 1\n```\n\n```yaml agent-plan\nversion: 1\n```\n"
    with pytest.raises(plan.PlanError):
        plan.extract(text)


def test_extract_reads_a_block_with_crlf_line_endings():
    text = "intro\r\n```yaml agent-plan\r\nversion: 1\r\nkind: story\r\n```\r\n"
    assert plan.extract(text)["kind"] == "story"


def test_sync_is_idempotent():
    s = story("S1", ["app/**"], [track("main", ["app/**"])])
    import yaml
    body = "intro\n\n```yaml agent-plan\n" + yaml.safe_dump(s) + "```\n"
    once = plan.sync(body, s)
    assert plan.sync(once, s) == once


# ── epic ↔ story consistency ─────────────────────────────────────────────────

def test_rejects_a_story_plan_that_owns_more_than_its_epic_entry():
    e = three_story_epic()
    ss = stories_for(e)
    ss[0]["owns"] = ["backend/**", "backend/pyproject.toml", "infra/cron.yaml"]
    ss[0]["tracks"][0]["owns"] = ["backend/**"]
    assert any("infra/cron.yaml" in x and "epic" in x for x in plan.validate_set(e, ss))


def test_accepts_a_story_plan_narrower_than_its_epic_entry():
    e = three_story_epic()
    ss = stories_for(e)
    ss[0]["owns"] = ["backend/app/reports/**"]
    ss[0]["tracks"][0]["owns"] = ["backend/app/reports/**"]
    assert plan.validate_set(e, ss) == []


def test_rejects_a_story_plan_whose_dependencies_differ_from_the_epic():
    e = three_story_epic()
    ss = stories_for(e)
    ss[2]["depends_on"] = ["S1"]  # the epic says S1 and S2
    assert any("depends_on" in x for x in plan.validate_set(e, ss))


# ── scaffold ─────────────────────────────────────────────────────────────────

TEMPLATE = (HERE.parent.parent / "templates" / "epic" / "story-shell.md").read_text(encoding="utf-8")


def epic_md(e, prose=""):
    import yaml
    return prose + "\n\n```yaml agent-plan\n" + yaml.safe_dump(e, sort_keys=False) + "```\n"


def scaffolded(e, prose=""):
    return {sid: plan.extract(body) for sid, body in plan.scaffold(epic_md(e, prose), TEMPLATE).items()}


def test_scaffold_writes_one_story_per_epic_story_and_the_set_validates():
    e = three_story_epic()
    out = scaffolded(e)
    assert sorted(out) == ["S1", "S2", "S3"]
    assert plan.validate_set(e, list(out.values())) == []


def test_scaffold_forbids_what_parallel_stories_own():
    out = scaffolded(three_story_epic())
    assert out["S1"]["must_not_touch"] == ["frontend/**"]   # S2 runs alongside S1
    assert out["S2"]["must_not_touch"] == ["backend/**"]


def test_scaffold_does_not_forbid_what_ordered_stories_own():
    # S3 runs after S1 and S2, so their paths are not off limits to it.
    assert scaffolded(three_story_epic())["S3"]["must_not_touch"] == []


def test_scaffold_copies_ownership_dependencies_and_verify_from_the_epic():
    s3 = scaffolded(three_story_epic())["S3"]
    assert s3["owns"] == ["docs/**"] and s3["depends_on"] == ["S1", "S2"] and s3["verify"] == "make test"
    assert s3["tracks"] == [{"id": "main", "kind": "track", "owns": ["docs/**"], "verify": "make test"}]


def test_scaffold_names_branches_from_type_issue_and_title():
    e = three_story_epic()
    e["stories"][0].update(type="bug", issue="#41", title="Empty CSV has no header!")
    assert scaffolded(e)["S1"]["branch"] == "fix/41-empty-csv-has-no-header"
    assert scaffolded(e)["S2"]["branch"] == "feat/s2-story-s2"   # no issue number yet


def test_scaffold_copies_ac_wording_from_the_epic_prose():
    prose = "**Acceptance criteria**\n\n- **AC1:** When X, then Y, so that Z.\n- **AC2:** …\n- **AC3:** …\n"
    assert scaffolded(three_story_epic(), prose)["S1"]["ac_text"] == {"AC1": "When X, then Y, so that Z."}


def test_scaffold_refuses_an_epic_that_does_not_validate():
    e = three_story_epic()
    e["stories"][1]["owns"] = ["backend/**"]  # overlaps S1 in parallel
    with pytest.raises(plan.PlanError):
        plan.scaffold(epic_md(e), TEMPLATE)


def test_scaffold_output_passes_the_prose_shape_check():
    va = plan._validate_artifact()
    for body in plan.scaffold(epic_md(three_story_epic()), TEMPLATE).values():
        assert va.check_story(body) == []


# ── check ────────────────────────────────────────────────────────────────────

def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


EPIC_TEMPLATE = (HERE.parent.parent / "templates" / "epic" / "epic-shell.md").read_text(encoding="utf-8")


def full_epic_md(e):
    import yaml
    return plan.FENCE.sub(lambda _: "```yaml agent-plan\n" + yaml.safe_dump(e, sort_keys=False) + "```",
                          EPIC_TEMPLATE, count=1)


def test_check_passes_and_syncs_a_good_set(tmp_path):
    e = three_story_epic()
    paths = [write(tmp_path, "epic.md", full_epic_md(e))]
    for sid, body in plan.scaffold(epic_md(e), TEMPLATE).items():
        paths.append(write(tmp_path, f"story-{sid}.md", body))
    ok, lines = plan.check(paths)
    assert ok, lines
    assert any(line.startswith("synced") and "epic.md" in line for line in lines)
    assert "| S3 |" in (tmp_path / "epic.md").read_text()  # generated story table


def test_check_fails_on_a_plan_error_and_writes_nothing(tmp_path):
    e = three_story_epic()
    e["stories"][1]["owns"] = ["backend/**"]
    path = write(tmp_path, "epic.md", epic_md(e))
    before = (tmp_path / "epic.md").read_text()
    ok, lines = plan.check([path])
    assert not ok and any("can run in parallel" in x for x in lines)
    assert (tmp_path / "epic.md").read_text() == before


def test_check_fails_on_missing_prose_sections(tmp_path):
    e = three_story_epic()
    body = plan.scaffold(epic_md(e), TEMPLATE)["S1"].replace("**Context**", "**Background**")
    ok, lines = plan.check([write(tmp_path, "story-S1.md", body)])
    assert not ok and any("missing **Context**" in x for x in lines)


# ── review findings from #90 (#91) ───────────────────────────────────────────

import subprocess  # noqa: E402
import sys  # noqa: E402

PLAN_PY = HERE.parent / "plan.py"


@pytest.mark.parametrize("field, snippet", [
    ("tracks", "kind: story\nstory: S1\ntracks: [main]\n"),
    ("stories", "kind: epic\nstories: [S1]\n"),
    ("tasks", "kind: story\nstory: S1\ntracks:\n- id: main\ntasks: [T1]\n"),
    ("contracts", "kind: epic\ncontracts: [C1]\nstories: []\n"),
])
def test_rejects_a_scalar_where_an_entry_needs_fields(field, snippet):
    with pytest.raises(plan.PlanError, match=field):
        plan.extract("```yaml agent-plan\nversion: 1\n" + snippet + "```\n")


def test_rejects_an_undecodable_file_as_a_plan_error(tmp_path):
    bad = tmp_path / "plan.md"
    bad.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(plan.PlanError):
        plan.read_text(str(bad))


def test_accepts_a_bare_yaml_plan_that_starts_with_a_comment():
    assert plan.extract("# plan for the export epic\nversion: 1\nkind: epic\nstories: []\n")["kind"] == "epic"


def test_rejects_markdown_without_a_plan_block():
    with pytest.raises(plan.PlanError, match="no ```yaml agent-plan block"):
        plan.extract("# Epic: export\n\nSome prose.\n")


@pytest.mark.parametrize("args", [["sync", "-"], ["status", "-", "--track", "main", "--set", "done"],
                                  ["check", "-"]])
def test_rejects_rewriting_stdin(tmp_path, args):
    out = subprocess.run([sys.executable, str(PLAN_PY), *args], cwd=tmp_path, input="x", capture_output=True, text=True)
    assert out.returncode == 2 and "stdin" in (out.stdout + out.stderr)
    assert not (tmp_path / "-").exists()


def test_rejects_duplicate_task_ids():
    s = story("S1", ["a/**"], [track("main", ["a/**"])],
              tasks=[task("T1", "main", ["a/x.py"]), task("T1", "main", ["a/y.py"])])
    assert any("duplicate task ids" in x for x in plan.validate_story(s))


def test_rejects_scheduling_dependants_of_an_unplanned_story_in_a_wave():
    e = three_story_epic()
    s3 = story("S3", ["docs/**"], [track("main", ["docs/**"])], acs=["AC3"], depends_on=["S1", "S2"])
    nodes, deps = plan.units(e, [s3])
    levels = plan.topo_levels(list(nodes), deps, "tracks")
    assert "S3/main" not in [u for level in levels for u in level]
    assert plan.waiting_on_unplanned(list(nodes), deps) == ["S3/main"]


@pytest.mark.parametrize("limit", [0, -1])
def test_rejects_scheduling_anything_with_no_capacity(limit):
    s = story("S1", ["a/**"], [track("main", ["a/**"])])
    assert plan.next_runnable(None, [s], limit) == []


def test_rejects_scaffolding_an_unknown_story_id():
    e = three_story_epic()
    with pytest.raises(plan.PlanError, match="S9"):
        plan.scaffold(epic_md(e), TEMPLATE, only=["S9"])


def test_accepts_a_status_change_that_keeps_comments_and_layout():
    text = ("Part of #1\n\n```yaml agent-plan\n"
            "version: 1\nkind: story\nstory: S1\n"
            "# why this story exists: a comment the planner wrote\n"
            "acs: [AC1]\nowns: [a/**]\nverify: make test\n"
            "tracks:\n"
            "  - id: main   # the only track\n"
            "    owns: [a/**]\n"
            "    verify: make test-main\n"
            "    status: todo\n"
            "```\n")
    new = plan.set_status(text, "main", "blocked", "needs: a decision, #3")
    assert "# why this story exists: a comment the planner wrote" in new
    assert "- id: main   # the only track" in new
    assert "acs: [AC1]" in new
    track_ = plan.extract(new)["tracks"][0]
    assert track_["status"] == "blocked" and track_["note"] == "needs: a decision, #3"
    again = plan.set_status(new, "main", "done", "merged abc")
    t2 = plan.extract(again)["tracks"][0]
    assert (t2["status"], t2["note"]) == ("done", "merged abc")
    assert again.count("note:") == 1
