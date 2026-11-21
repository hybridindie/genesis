"""tracker.py: issue references, remotes and failures must never hit the wrong issue."""

from __future__ import annotations

import importlib.util
import urllib.error
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tracker", HERE.parent / "tracker.py")
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


@pytest.mark.parametrize(("ref", "want"), [
    ("#13", "13"), ("13", "13"), (" 13 ", "13"),
    ("https://github.com/o/r/issues/13", "13"),
    ("https://github.com/o/r/issues/13?page=2", "13"),
    ("https://github.com/o/r/issues/13#issuecomment-987654321", "13"),
    ("https://git.example.com/o/r/issues/7/", "7"),
])
def test_accepts_issue_references(ref, want):
    assert tracker.number(ref) == want


@pytest.mark.parametrize("ref", ["abc", "https://github.com/o/r/pull/13x", "#"])
def test_rejects_what_is_not_an_issue_reference(ref):
    with pytest.raises(SystemExit, match="not an issue reference"):
        tracker.number(ref)


@pytest.mark.parametrize(("url", "want"), [
    ("git@github.com:o/r.git", ("github.com", "https://github.com", "o", "r")),
    ("https://github.com/o/r", ("github.com", "https://github.com", "o", "r")),
    ("ssh://git@git.example.com:2222/o/r.git", ("git.example.com", "https://git.example.com", "o", "r")),
    ("https://git.example.com:3000/o/r.git", ("git.example.com", "https://git.example.com:3000", "o", "r")),
    ("https://user@git.example.com/gitea/o/r.git", ("git.example.com", "https://git.example.com/gitea", "o", "r")),
])
def test_parses_remotes_keeping_port_and_subpath(url, want):
    assert tracker.parse_remote(url) == want


def test_rejects_an_unknown_tracker_override(monkeypatch):
    monkeypatch.setenv("TRACKER", "gitub")
    monkeypatch.setattr(tracker, "remote", lambda: ("github.com", "https://github.com", "o", "r"))
    with pytest.raises(SystemExit, match="TRACKER"):
        tracker.forge()


def test_accepts_a_tracker_override_in_any_case(monkeypatch):
    monkeypatch.setenv("TRACKER", "GitHub")
    monkeypatch.setattr(tracker, "remote", lambda: ("git.example.com", "https://git.example.com", "o", "r"))
    assert isinstance(tracker.forge(), tracker.GitHub)


def test_reports_a_network_failure_as_a_tracker_error(monkeypatch):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    def down(*_a, **_k):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(tracker.urllib.request, "urlopen", down)
    g = tracker.Gitea("https://git.example.com", "o", "r")
    with pytest.raises(SystemExit, match="tracker: Gitea GET"):
        g.get("1")


def test_reports_an_unreadable_body_file_as_a_tracker_error(monkeypatch, tmp_path):
    monkeypatch.setattr(tracker, "forge", lambda: tracker.GitHub())
    monkeypatch.setattr(tracker.sys, "argv", ["tracker.py", "put", "#1", str(tmp_path / "missing.md")])
    with pytest.raises(SystemExit, match="tracker: cannot read"):
        tracker.main()
