"""Reviewer detection for the ship-pr watcher.

The watcher used to wait only for names it knew, which missed the App that
actually posts, and cached an empty first poll, which settled before the review.
"""

from __future__ import annotations

import pytest

from conftest import load

watch = load("templates/_shared/skills/ship-pr/scripts/watch_pr.py", "watch")


def test_matches_a_prefixed_bot_login():
    assert watch.matches_bot("acme-ocr[bot]", ("ocr",))
    assert watch.matches_bot("ocr-reviewer[bot]", ("ocr",))


def test_does_not_match_a_word_that_merely_contains_the_name():
    assert not watch.matches_bot("mediocre-dev", ("ocr",))


def test_any_bot_is_a_reviewer_except_reporters():
    assert watch.is_reviewer("some-new-reviewer[bot]", watch.KNOWN_REVIEWERS)
    assert watch.is_reviewer("some-new-reviewer", watch.KNOWN_REVIEWERS)  # gh strips [bot]
    assert watch.is_reviewer("acme-reviewer", watch.KNOWN_REVIEWERS)
    assert not watch.is_reviewer("dependabot[bot]", watch.KNOWN_REVIEWERS)
    assert not watch.is_reviewer("renovate[bot]", watch.KNOWN_REVIEWERS)
    assert not watch.is_reviewer("johnd", watch.KNOWN_REVIEWERS)


def test_env_override_wins_and_none_disables(monkeypatch):
    monkeypatch.setenv("SHIP_PR_BOTS", "My-App[bot]")
    assert watch.bot_names() == ("my-app[bot]",)
    monkeypatch.setenv("SHIP_PR_BOTS", "none")
    assert watch.bot_names() == ()


def test_marker_enables_waiting(tmp_path, monkeypatch):
    monkeypatch.delenv("SHIP_PR_BOTS", raising=False)
    monkeypatch.chdir(tmp_path)
    assert watch.bot_names({"reviews": [], "comments": []}) == ()
    (tmp_path / ".opencodereview").mkdir()
    (tmp_path / ".opencodereview" / "rule.json").write_text('{"rules": []}')
    assert watch.bot_names({"reviews": [], "comments": []})


def test_history_enables_waiting_without_a_marker(tmp_path, monkeypatch):
    monkeypatch.delenv("SHIP_PR_BOTS", raising=False)
    monkeypatch.chdir(tmp_path)
    pr = {"reviews": [], "comments": [{"author": {"login": "anything-reviewer[bot]"}}]}
    assert watch.bot_names(pr)


def test_waits_until_a_review_lands_after_the_last_commit():
    pr = {
        "state": "OPEN",
        "reviews": [{"author": {"login": "ocr-reviewer[bot]"}, "submittedAt": "2026-01-01T10:00:00Z"}],
        "comments": [],
        "commits": [{"committedDate": "2026-01-01T11:00:00Z"}],
    }
    code, status, _ = watch.evaluate(pr, {"pass": 1, "pending": 0, "fail": 0, "cancel": 0, "skipping": 0, "total": 1}, ("ocr",))
    assert code is None and status == "waiting"


def test_settles_when_the_review_is_newer_than_the_commit():
    pr = {
        "state": "OPEN",
        "reviews": [{"author": {"login": "ocr-reviewer[bot]"}, "submittedAt": "2026-01-01T12:00:00Z"}],
        "comments": [],
        "commits": [{"committedDate": "2026-01-01T11:00:00Z"}],
    }
    code, status, _ = watch.evaluate(pr, {"pass": 1, "pending": 0, "fail": 0, "cancel": 0, "skipping": 0, "total": 1}, ("ocr",))
    assert code == 0 and status == "settled"


def test_failing_checks_win_over_the_review():
    pr = {"state": "OPEN", "reviews": [], "comments": [], "commits": []}
    code, status, _ = watch.evaluate(pr, {"pass": 0, "pending": 0, "fail": 1, "cancel": 0, "skipping": 0, "total": 1}, ())
    assert code == 10 and status == "ci_failed"



OLD_HEAD = {"state": "OPEN", "reviews": [], "comments": [], "commits": [{"committedDate": "2026-01-01T11:00:00Z"}]}
EMPTY = {"pass": 0, "pending": 0, "fail": 0, "cancel": 0, "skipping": 0, "total": 0}


@pytest.mark.parametrize("ci_dir", [".github/workflows", ".gitea/workflows"])
def test_an_empty_check_list_is_pending_when_the_repo_defines_ci(tmp_path, monkeypatch, ci_dir):
    # A retargeted PR has no checks: `pull_request` does not fire on a base edit.
    # Settling would let it merge untested, however old its head commit is.
    (tmp_path / ci_dir).mkdir(parents=True)
    (tmp_path / ci_dir / "ci.yml").write_text("on: pull_request\n")
    monkeypatch.chdir(tmp_path)
    code, status, message = watch.evaluate(OLD_HEAD, EMPTY, ())
    assert code is None and status == "waiting"
    assert "reopen" in message
    code, status, _ = watch.evaluate(OLD_HEAD, None, ())
    assert code is None and status == "waiting"


def test_an_empty_check_list_settles_when_the_repo_has_no_ci(tmp_path, monkeypatch):
    # A project rendered with --no-ci has no workflows; waiting would never end.
    (tmp_path / ".github").mkdir()  # a .github dir without workflows is not CI
    monkeypatch.chdir(tmp_path)
    code, status, message = watch.evaluate(OLD_HEAD, None, ())
    assert code == 0 and status == "settled"
    assert "no CI" in message


def test_ci_is_found_from_a_subdirectory_of_the_repo(tmp_path, monkeypatch):
    # gh resolves the repo from any subdirectory; the workflow scan must too.
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text("on: pull_request\n")
    (tmp_path / "src").mkdir()
    monkeypatch.chdir(tmp_path / "src")
    code, status, _ = watch.evaluate(OLD_HEAD, EMPTY, ())
    assert code is None and status == "waiting"


@pytest.mark.parametrize("state", ["DIRTY", "BEHIND"])
def test_a_conflicted_pr_with_no_checks_is_blocked_not_waiting(tmp_path, monkeypatch, state):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text("on: pull_request\n")
    monkeypatch.chdir(tmp_path)
    code, status, _ = watch.evaluate(dict(OLD_HEAD, mergeStateStatus=state), EMPTY, ())
    assert code == 30 and status == "blocked"
