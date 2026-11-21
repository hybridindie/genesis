"""End-to-end tests for dispatch.py against throwaway git repositories.

Same naming as the other calibration tests: test_accepts_* must succeed,
test_rejects_* must refuse (a failure there means the dispatcher is too lax).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

DISPATCH = Path(__file__).resolve().parent.parent / "dispatch.py"


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def commit(cwd, message, **files):
    for name, text in files.items():
        p = Path(cwd) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    sh("git", "add", "-A", cwd=cwd)
    sh("git", "commit", "-qm", message, cwd=cwd)


def body(block):
    return "Part of #1\n\n```yaml agent-plan\n" + yaml.safe_dump(block, sort_keys=False) + "```\n"


EPIC = {"version": 1, "kind": "epic", "epic": "#1", "acs": ["AC1", "AC2", "AC3"], "stories": [
    {"id": "S1", "title": "api", "size": "M", "acs": ["AC1"], "owns": ["app/**"], "verify": "true"},
    {"id": "S2", "title": "docs", "size": "S", "acs": ["AC2"], "owns": ["docs/**"], "verify": "true"},
    {"id": "S3", "title": "ui", "size": "S", "acs": ["AC3"], "owns": ["ui/**"], "verify": "true",
     "depends_on": ["S1"]},
]}
S1 = {"version": 1, "kind": "story", "story": "S1", "branch": "feat/s1-api", "acs": ["AC1"],
      "owns": ["app/**"], "verify": "test -f app/a.py", "tracks": [
          {"id": "contract", "kind": "contract", "owns": ["app/types.py"], "verify": "test -f app/types.py"},
          {"id": "A", "owns": ["app/a.py"], "depends_on": ["contract"], "verify": "test -f app/a.py"},
          {"id": "B", "owns": ["app/b.py"], "depends_on": ["contract"], "verify": "test -f app/b.py"}],
      "integration": {"merge_order": ["contract", "A", "B"], "verify": "test -f app/b.py"}}
S2 = {"version": 1, "kind": "story", "story": "S2", "branch": "feat/s2-docs", "acs": ["AC2"],
      "owns": ["docs/**"], "verify": "true", "tracks": [{"id": "main", "owns": ["docs/**"], "verify": "true"}]}
S3 = {"version": 1, "kind": "story", "story": "S3", "branch": "feat/s3-ui", "acs": ["AC3"], "depends_on": ["S1"],
      "owns": ["ui/**"], "verify": "true", "tracks": [{"id": "main", "owns": ["ui/**"], "verify": "true"}]}


@pytest.fixture(autouse=True)
def hermetic_git(monkeypatch):
    """Ignore the developer's git config: CI runners have no identity, so a
    test that passes only with one is a test that fails in CI."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    sh("git", "init", "-q", "-b", "main", cwd=root)
    sh("git", "config", "user.email", "t@t", cwd=root)   # shared by every worktree
    sh("git", "config", "user.name", "t", cwd=root)
    commit(root, "init", **{"README.md": "x\n"})
    plans = tmp_path / "plans"
    plans.mkdir()
    for name, block in [("epic.md", EPIC), ("story-S1.md", S1), ("story-S2.md", S2), ("story-S3.md", S3)]:
        (plans / name).write_text(body(block))
    return root, plans


def run(root, *args, expect=None):
    out = subprocess.run([sys.executable, str(DISPATCH), *args], cwd=root, capture_output=True, text=True)
    data = json.loads(out.stdout)
    if expect is not None:
        assert out.returncode == expect, data
    return data


def load(root, plans):
    return run(root, "load", "--files", *sorted(str(p) for p in plans.iterdir()), expect=0)


def status(plans, sid, track):
    block = yaml.safe_load((plans / f"story-{sid}.md").read_text().split("```yaml agent-plan\n")[1].split("```")[0])
    return next(t for t in block["tracks"] if t["id"] == track).get("status", "todo")


def work_in(root, sid, track, msg="work", **files):
    tree = root.parent / f"{root.name}-tracks" / f"{sid}-{track}"
    commit(tree, msg, **files)
    return tree


# ── load / prepare ───────────────────────────────────────────────────────────

def test_accepts_load_and_reports_unplanned_stories(repo):
    root, plans = repo
    (plans / "story-S3.md").unlink()
    data = load(root, plans)
    assert data["unplanned_stories"] == ["S3"] and data["base"] == "main"


def test_rejects_prepare_with_a_dirty_checkout(repo):
    root, plans = repo
    load(root, plans)
    (root / "stray.txt").write_text("x")
    assert "uncommitted" in run(root, "prepare", expect=2)["error"]


def test_accepts_prepare_dry_run_without_touching_git(repo):
    root, plans = repo
    load(root, plans)
    data = run(root, "prepare", "--plan", expect=0)
    assert [u["unit"] for u in data["units"]] == ["S1/contract", "S2/main"]
    assert sh("git", "branch", "--list", cwd=root).split() == ["*", "main"]
    assert status(plans, "S1", "contract") == "todo"
    assert all(Path(u["brief"]).is_file() for u in data["units"])


# ── weak checks (#72): a verify that passes before any work cannot fail ─────

def test_accepts_prepare_flagging_a_verify_that_already_passes(repo):
    root, plans = repo
    load(root, plans)
    units = {u["unit"]: u for u in run(root, "prepare", expect=0)["units"]}
    assert units["S1/contract"]["baseline"] == "fail" and not units["S1/contract"]["weak_check"]
    assert units["S2/main"]["baseline"] == "pass" and units["S2/main"]["weak_check"]
    assert "already passes" in Path(units["S2/main"]["brief"]).read_text()
    assert "already passes" not in Path(units["S1/contract"]["brief"]).read_text()


def test_rejects_a_weak_check_when_the_diff_changes_no_test(repo):
    root, plans = repo
    load(root, plans)
    run(root, "prepare", expect=0)
    work_in(root, "S2", "main", **{"docs/guide.md": "x\n"})
    data = run(root, "check", "S2/main", expect=1)
    assert any("cannot fail" in f for f in data["findings"])


def test_accepts_a_weak_check_once_the_diff_adds_a_test(repo):
    root, plans = repo
    load(root, plans)
    run(root, "prepare", expect=0)
    work_in(root, "S2", "main", **{"docs/guide.md": "x\n", "docs/tests/test_guide.py": "def test(): pass\n"})
    assert run(root, "check", "S2/main", expect=0)["ok"]


def test_accepts_a_refactor_track_that_declares_a_passing_baseline(repo):
    root, plans = repo
    s2 = dict(S2, tracks=[dict(S2["tracks"][0], verify_baseline="pass")])
    (plans / "story-S2.md").write_text(body(s2))
    load(root, plans)
    units = {u["unit"]: u for u in run(root, "prepare", expect=0)["units"]}
    assert not units["S2/main"]["weak_check"]
    work_in(root, "S2", "main", **{"docs/guide.md": "x\n"})
    assert run(root, "check", "S2/main", expect=0)["ok"]


def test_accepts_prepare_creating_worktrees_and_marking_units_running(repo):
    root, plans = repo
    load(root, plans)
    data = run(root, "prepare", expect=0)
    for u in data["units"]:
        assert Path(u["worktree"]).is_dir()
        assert sh("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=u["worktree"]).strip() == u["branch"]
    assert status(plans, "S1", "contract") == "running"   # written back to the source file
    assert "Where to work" in Path(data["units"][0]["brief"]).read_text()


def test_rejects_preparing_the_same_units_twice(repo):
    root, plans = repo
    load(root, plans)
    run(root, "prepare", expect=0)
    assert run(root, "prepare", expect=0)["units"] == []


# ── check ────────────────────────────────────────────────────────────────────

def prepared(repo):
    root, plans = repo
    load(root, plans)
    run(root, "prepare", expect=0)
    return root, plans


def test_accepts_check_of_in_scope_work_that_verifies(repo):
    root, _ = prepared(repo)
    work_in(root, "S1", "contract", **{"app/types.py": "T = 1\n"})
    data = run(root, "check", "S1/contract", expect=0)
    assert data["changed"] == ["app/types.py"] and data["verify_passed"] is True


def test_rejects_check_of_work_outside_owns_and_still_runs_verify(repo):
    root, _ = prepared(repo)
    work_in(root, "S1", "contract", **{"app/types.py": "T = 1\n", "uv.lock": "lock\n"})
    data = run(root, "check", "S1/contract", expect=1)
    assert data["outside_owns"] == ["uv.lock"] and data["verify_passed"] is True


def test_rejects_check_of_a_track_with_no_commits(repo):
    root, _ = prepared(repo)
    assert "no commits on the track branch" in run(root, "check", "S1/contract", expect=1)["findings"]


def test_rejects_check_of_uncommitted_work_without_running_verify(repo):
    root, _ = prepared(repo)
    tree = work_in(root, "S1", "contract", **{"app/types.py": "T = 1\n"})
    (tree / "app" / "extra.py").write_text("x\n")
    data = run(root, "check", "S1/contract", expect=1)
    assert data["verify_passed"] is None and any("uncommitted" in f for f in data["findings"])


def test_accepts_check_restoring_files_the_verify_run_wrote(repo):
    root, plans = repo
    s1 = yaml.safe_load(body(S1).split("```yaml agent-plan\n")[1].split("```")[0])
    s1["tracks"][0]["verify"] = "test -f app/types.py && echo cache > app/cache.txt"
    (plans / "story-S1.md").write_text(body(s1))
    prepared(repo)
    tree = work_in(root, "S1", "contract", **{"app/types.py": "T = 1\n"})
    run(root, "check", "S1/contract", expect=0)
    assert not (tree / "app" / "cache.txt").exists()


# ── merge ────────────────────────────────────────────────────────────────────

def finish(root, unit, **files):
    sid, track = unit.split("/")
    work_in(root, sid, track, **files)
    run(root, "check", unit, expect=0)
    return run(root, "merge", unit)


def test_accepts_merge_and_cleans_up_the_track(repo):
    root, plans = prepared(repo)
    data = finish(root, "S1/contract", **{"app/types.py": "T = 1\n"})
    assert data["ok"] and status(plans, "S1", "contract") == "done"
    assert not (root.parent / "proj-tracks" / "S1-contract").exists()
    assert "app/types.py" in sh("git", "ls-tree", "-r", "--name-only", "feat/s1-api", cwd=root)


def test_rejects_a_failed_merge_without_blaming_the_plan(repo):
    # A merge that fails for an environment reason (here: no committer
    # identity) is an error to fix, not a conflict that blocks the track.
    root, plans = prepared(repo)
    work_in(root, "S1", "contract", **{"app/types.py": "T = 1\n"})
    run(root, "check", "S1/contract", expect=0)
    sh("git", "config", "--unset", "user.email", cwd=root)
    sh("git", "config", "--unset", "user.name", cwd=root)
    data = run(root, "merge", "S1/contract", expect=2)
    assert "identity" in data["error"].lower() and "conflict" not in data["error"]
    assert status(plans, "S1", "contract") == "running"


def test_accepts_the_next_wave_after_the_contract_merges(repo):
    root, _ = prepared(repo)
    finish(root, "S1/contract", **{"app/types.py": "T = 1\n"})
    units = [u["unit"] for u in run(root, "prepare", expect=0)["units"]]
    assert units == ["S1/A", "S1/B"]
    tree = root.parent / "proj-tracks" / "S1-A"
    assert (tree / "app" / "types.py").is_file()   # tracks start from the merged contract


def test_rejects_merging_ahead_of_merge_order(repo):
    root, _ = prepared(repo)
    finish(root, "S1/contract", **{"app/types.py": "T = 1\n"})
    run(root, "prepare", expect=0)
    work_in(root, "S1", "B", **{"app/b.py": "b\n"})
    data = run(root, "merge", "S1/B", expect=1)
    assert data["findings"] == ["merge A first"]


def test_rejects_a_merge_conflict_by_blocking_the_track(repo):
    root, plans = prepared(repo)
    finish(root, "S1/contract", **{"app/types.py": "T = 1\n"})
    run(root, "prepare", expect=0)
    # Both tracks edit the contract file (outside their owns): A merges, B conflicts.
    work_in(root, "S1", "A", **{"app/a.py": "a\n", "app/types.py": "T = 'a'\n"})
    assert run(root, "merge", "S1/A", expect=0)["ok"]
    work_in(root, "S1", "B", **{"app/b.py": "b\n", "app/types.py": "T = 'b'\n"})
    data = run(root, "merge", "S1/B", expect=1)
    assert "app/types.py" in data["findings"][0] and status(plans, "S1", "B") == "blocked"


def test_rejects_merging_a_unit_that_is_not_running(repo):
    root, plans = repo
    load(root, plans)
    assert "not running" in run(root, "merge", "S1/A", expect=2)["error"]


# ── dependent stories, integrate, report ─────────────────────────────────────

def complete_s1(root):
    finish(root, "S1/contract", **{"app/types.py": "T = 1\n"})
    run(root, "prepare", expect=0)
    finish(root, "S1/A", **{"app/a.py": "a\n"})
    finish(root, "S1/B", **{"app/b.py": "b\n"})


def test_accepts_a_dependent_story_starting_from_its_upstream_work(repo):
    root, _ = prepared(repo)
    complete_s1(root)
    units = [u["unit"] for u in run(root, "prepare", expect=0)["units"]]
    assert "S3/main" in units
    assert (root.parent / "proj-tracks" / "S3-main" / "app" / "b.py").is_file()


def test_rejects_integrating_a_story_with_unfinished_tracks(repo):
    root, _ = prepared(repo)
    assert run(root, "integrate", "S1", expect=1)["findings"] == ["tracks not done: contract, A, B"]


def test_accepts_integrating_a_finished_story(repo):
    root, _ = prepared(repo)
    complete_s1(root)
    data = run(root, "integrate", "S1", expect=0)
    assert [c["passed"] for c in data["checks"]] == [True, True]


def test_accepts_report_with_counts_and_next_units(repo):
    root, _ = prepared(repo)
    data = run(root, "report", expect=0)
    assert data["counts"]["running"] == 2 and data["next_runnable"] == []
    assert any(w.startswith("S1/A waits on S1/contract") for w in data["waiting"])


def test_accepts_block_with_a_note(repo):
    root, plans = prepared(repo)
    run(root, "block", "S2/main", "--note", "needs a docs owner", expect=0)
    assert status(plans, "S2", "main") == "blocked"


# ── retry (#73): send the unit back with its evidence, capped at 3 attempts ──

def failing_contract(repo):
    root, plans = prepared(repo)
    assert not run(root, "check", "S1/contract", expect=1)["ok"]   # nothing done: verify fails
    return root, plans


def test_accepts_a_retry_that_returns_the_evidence_and_keeps_the_worktree(repo):
    root, plans = failing_contract(repo)
    data = run(root, "retry", "S1/contract", "--note", "create app/types.py", expect=0)
    assert data["attempt"] == 2 and data["max_attempts"] == 3
    brief = Path(data["brief"]).read_text()
    assert "Attempt 2 of 3" in brief and "verify failed" in brief and "create app/types.py" in brief
    assert "only" in brief.lower()                                   # scope restated
    assert (root.parent / "proj-tracks" / "S1-contract").is_dir()   # the worktree is kept
    assert status(plans, "S1", "contract") == "running"


def test_accepts_a_retry_that_fixes_the_unit(repo):
    root, _ = failing_contract(repo)
    run(root, "retry", "S1/contract", "--note", "create app/types.py", expect=0)
    work_in(root, "S1", "contract", "fix", **{"app/types.py": "T = 1\n"})
    assert run(root, "check", "S1/contract", expect=0)["ok"]


def test_rejects_a_retry_that_widens_its_scope(repo):
    root, _ = failing_contract(repo)
    run(root, "retry", "S1/contract", "--note", "create app/types.py", expect=0)
    work_in(root, "S1", "contract", "fix", **{"app/types.py": "T = 1\n", "app/extra.py": "y = 2\n"})
    data = run(root, "check", "S1/contract", expect=1)
    assert any("widened" in f and "app/extra.py" in f for f in data["findings"])


def test_rejects_a_fourth_attempt_and_routes_the_unit_to_replanning(repo):
    root, plans = failing_contract(repo)
    for attempt in (2, 3):
        assert run(root, "retry", "S1/contract", "--note", "try again", expect=0)["attempt"] == attempt
        run(root, "check", "S1/contract", expect=1)
    data = run(root, "retry", "S1/contract", "--note", "try again", expect=1)
    assert data["replan"] and status(plans, "S1", "contract") == "blocked"
    assert "S1/contract" in run(root, "report", expect=0)["needs_replan"]


def test_rejects_retrying_a_unit_that_has_not_been_checked(repo):
    root, _ = prepared(repo)
    assert "check" in run(root, "retry", "S1/contract", "--note", "x", expect=2)["error"]
