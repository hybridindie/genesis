"""Reviewer detection for the ship-pr watcher.

The watcher used to wait only for names it knew, which missed the App that
actually posts, and cached an empty first poll, which settled before the review.
"""

from __future__ import annotations

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
