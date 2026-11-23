"""tracker.py: issue references, remotes and failures must never hit the wrong issue."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
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


def test_tracker_github_does_not_need_a_parseable_remote(monkeypatch):
    monkeypatch.setenv("TRACKER", "github")
    def boom():
        raise AssertionError("remote() should not be called")
    monkeypatch.setattr(tracker, "remote", boom)
    assert isinstance(tracker.forge(), tracker.GitHub)


def test_reports_a_non_json_response_as_a_tracker_error(monkeypatch):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    class Page:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"<html>proxy error</html>"
    monkeypatch.setattr(tracker.urllib.request, "urlopen", lambda *a, **k: Page())
    with pytest.raises(SystemExit, match="tracker: Gitea GET"):
        tracker.Gitea("https://git.example.com", "o", "r").get("1")


def test_reports_a_hung_cli_as_a_tracker_error(monkeypatch):
    def hang(*_a, **_k):
        raise tracker.subprocess.TimeoutExpired("gh", 60)
    monkeypatch.setattr(tracker.subprocess, "run", hang)
    with pytest.raises(SystemExit, match="timed out"):
        tracker.sh("gh", "issue", "view", "1")


# --- labels, label and author -------------------------------------------------

SCRIPT = HERE.parent / "tracker.py"

FAKE_GH = '''#!{python}
"""A stand-in for gh: issue state lives in $FAKE_GH_STATE, calls go to $FAKE_GH_LOG."""
import json, os, sys
state_path = os.environ["FAKE_GH_STATE"]
state = json.load(open(state_path))
args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
def flag(name):
    return [args[i + 1] for i, a in enumerate(args) if a == name]
if args[:2] == ["issue", "view"]:
    issue = state["issues"][args[2]]
    field = flag("--json")[0]
    if field == "labels":
        print(json.dumps({{"labels": [{{"name": n}} for n in issue["labels"]]}}))
    elif field == "author":
        print(json.dumps({{"author": {{"login": issue["author"]}}}}))
    else:
        print(json.dumps({{field: issue.get(field, "")}}))
elif args[:2] == ["issue", "list"]:
    want = flag("--state")[0] if flag("--state") else "open"
    rows = [{{"number": int(k), "title": v.get("title", ""), "state": v.get("state", "open"),
             "labels": [{{"name": n}} for n in v["labels"]], "createdAt": v.get("createdAt", "")}}
            for k, v in state["issues"].items()]
    rows = [r for r in rows if want == "all" or r.pop("state") == want]
    for r in rows:
        r.pop("state", None)
    for name in flag("--label"):
        rows = [r for r in rows if name in [lb["name"] for lb in r["labels"]]]
    rows.sort(key=lambda r: r["createdAt"], reverse=True)  # gh lists newest first
    print(json.dumps(rows))
elif args[:2] == ["issue", "create"]:
    n = str(max(int(k) for k in state["issues"]) + 1)
    state["issues"][n] = {{"labels": [], "author": "octocat", "body": sys.stdin.read(), "title": flag("--title")[0]}}
    print(f"https://github.com/o/r/issues/{{n}}")
elif args[:2] == ["label", "list"]:
    if state.get("fail_label_list"):
        sys.exit("HTTP 502")
    print(json.dumps([{{"name": n}} for n in state["repo_labels"]]))
elif args[:2] == ["label", "create"]:
    if args[2] in state["repo_labels"]:
        sys.exit("label already exists")
    state["repo_labels"].append(args[2])
elif args[:2] == ["issue", "edit"]:
    issue = state["issues"][args[2]]
    for name in flag("--add-label"):
        if name not in state["repo_labels"]:
            sys.exit(f"could not add label: {{name!r}} not found")
        if name not in issue["labels"]:
            issue["labels"].append(name)
    for name in flag("--remove-label"):
        if name not in issue["labels"]:  # real gh fails on a label the issue lacks
            sys.exit(f"could not remove label: {{name!r}} not found")
        issue["labels"].remove(name)
else:
    sys.exit(f"fake gh: unexpected {{args}}")
json.dump(state, open(state_path, "w"))
'''


@pytest.fixture
def gh_repo(tmp_path):
    """A temporary git repo with a github.com origin and a fake gh first on PATH."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:o/r.git"], cwd=repo, check=True)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text(FAKE_GH.format(python=sys.executable))
    gh.chmod(0o755)
    state = tmp_path / "gh-state.json"
    state.write_text(json.dumps({
        "repo_labels": ["bug"],
        "issues": {"7": {"labels": ["bug"], "author": "octocat", "body": ""}},
    }))
    log = tmp_path / "gh-log.jsonl"
    log.write_text("")
    env = {k: v for k, v in os.environ.items()
           if k not in ("TRACKER", "GITEA_TOKEN", "TEA_TOKEN", "GITEA_URL")}
    env.update(PATH=f"{bindir}{os.pathsep}{env.get('PATH', '')}",
               FAKE_GH_STATE=str(state), FAKE_GH_LOG=str(log))

    class Repo:
        def run(self, *args):
            return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, env=env,
                                  capture_output=True, text=True, timeout=60)

        def state(self):
            return json.loads(state.read_text())

        def calls(self):
            return [json.loads(line) for line in log.read_text().splitlines()]

    r = Repo()
    r.state_path = state
    return r


def test_github_label_add_creates_a_missing_label_then_lists_it(gh_repo):
    out = gh_repo.run("label", "#7", "--add", "factory:running")
    assert out.returncode == 0, out.stderr
    assert "factory:running" in gh_repo.state()["repo_labels"]
    assert ["label", "create", "factory:running"] == gh_repo.calls()[1][:3]
    listed = gh_repo.run("labels", "#7")
    assert listed.returncode == 0, listed.stderr
    assert listed.stdout.splitlines() == ["bug", "factory:running"]


def test_github_label_add_reuses_an_existing_label_and_removes_others(gh_repo):
    out = gh_repo.run("label", "7", "--add", "bug")
    assert out.returncode == 0, out.stderr
    out = gh_repo.run("label", "7", "--add", "factory:queued", "factory:running", "--remove", "bug")
    assert out.returncode == 0, out.stderr
    assert gh_repo.state()["issues"]["7"]["labels"] == ["factory:queued", "factory:running"]
    creates = [c for c in gh_repo.calls() if c[:2] == ["label", "create"]]
    assert [c[2] for c in creates] == ["factory:queued", "factory:running"]


def test_github_label_remove_skips_a_label_the_issue_lacks(gh_repo):
    out = gh_repo.run("label", "7", "--remove", "factory:running")
    assert out.returncode == 0, out.stderr
    assert gh_repo.state()["issues"]["7"]["labels"] == ["bug"]
    assert not [c for c in gh_repo.calls() if c[:2] == ["issue", "edit"]]


def test_github_label_cleanup_can_repeat(gh_repo):
    for _ in range(2):
        out = gh_repo.run("label", "7", "--add", "factory:done", "--remove", "bug", "factory:running")
        assert out.returncode == 0, out.stderr
    assert gh_repo.state()["issues"]["7"]["labels"] == ["factory:done"]
    edits = [c for c in gh_repo.calls() if c[:2] == ["issue", "edit"]]
    assert all("factory:running" not in c for c in edits)


def test_github_label_remove_matches_case_insensitively(gh_repo):
    out = gh_repo.run("label", "7", "--remove", "BUG")
    assert out.returncode == 0, out.stderr
    assert gh_repo.state()["issues"]["7"]["labels"] == []


def test_github_label_remove_sends_case_differing_duplicates_once(gh_repo):
    out = gh_repo.run("label", "7", "--remove", "bug", "BUG")
    assert out.returncode == 0, out.stderr
    assert gh_repo.state()["issues"]["7"]["labels"] == []
    edit = [c for c in gh_repo.calls() if c[:2] == ["issue", "edit"]][-1]
    assert edit.count("--remove-label") == 1


def test_github_create_with_a_label_opens_the_issue_labelled(gh_repo, tmp_path):
    body = tmp_path / "epic.md"
    body.write_text("Epic body\n")
    out = gh_repo.run("create", "--title", "Epic: x", "--body-file", str(body), "--label", "factory:drafted")
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "#8"
    assert gh_repo.state()["issues"]["8"]["labels"] == ["factory:drafted"]


def test_create_prints_the_number_even_when_labelling_fails(gh_repo, tmp_path):
    body = tmp_path / "epic.md"
    body.write_text("Epic body\n")
    state = gh_repo.state()
    state["fail_label_list"] = True
    Path(gh_repo.state_path).write_text(json.dumps(state))
    out = gh_repo.run("create", "--title", "Epic: x", "--body-file", str(body), "--label", "factory:drafted")
    assert out.returncode != 0
    assert out.stdout.strip() == "#8"


def test_create_refuses_an_approval_label_before_opening_anything(gh_repo, tmp_path):
    body = tmp_path / "epic.md"
    body.write_text("Epic body\n")
    out = gh_repo.run("create", "--title", "Epic: x", "--body-file", str(body), "--label", "Factory:Approved")
    assert out.returncode == 2
    assert "person" in out.stderr
    assert gh_repo.calls() == []


def test_github_author_prints_the_opener_login(gh_repo):
    out = gh_repo.run("author", "https://github.com/o/r/issues/7")
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "octocat"


@pytest.mark.parametrize("protected", ["factory:approved", "factory:auto-approve",
                                       "Factory:Approved", "FACTORY:AUTO-APPROVE", " factory:approved "])
def test_label_add_refuses_a_label_only_a_person_applies(gh_repo, protected):
    out = gh_repo.run("label", "#7", "--add", "factory:running", protected)
    assert out.returncode == 2
    assert protected.strip() in out.stderr and "person" in out.stderr
    assert gh_repo.calls() == []
    assert gh_repo.state()["issues"]["7"]["labels"] == ["bug"]


@pytest.mark.parametrize("protected", ["factory:approved", "Factory:Auto-Approve"])
def test_label_remove_refuses_a_label_only_a_person_applies(gh_repo, protected):
    out = gh_repo.run("label", "#7", "--remove", protected)
    assert out.returncode == 2
    assert protected in out.stderr and "person" in out.stderr
    assert gh_repo.calls() == []


@pytest.mark.parametrize("names", [["--add", "factory: approved"], ["--add", "Factory:\tAuto-Approve"],
                                   ["--add", "bug", "--remove", " BUG "]])
def test_label_refuses_near_miss_approvals_and_add_remove_clashes(gh_repo, names):
    out = gh_repo.run("label", "#7", *names)
    assert out.returncode == 2, out.stderr
    assert gh_repo.calls() == []


def test_label_add_strips_names_so_no_near_duplicate_is_created(gh_repo):
    out = gh_repo.run("label", "7", "--add", " bug ")
    assert out.returncode == 0, out.stderr
    assert not [c for c in gh_repo.calls() if c[:2] == ["label", "create"]]


def test_forge_label_methods_enforce_the_guard_for_library_callers():
    for f in (tracker.GitHub(), object.__new__(tracker.Gitea)):
        with pytest.raises(tracker.LabelRefused):
            f.label("7", ["factory:approved"], [])
        with pytest.raises(tracker.LabelRefused):
            f.label("7", [], ["FACTORY:AUTO-APPROVE"])


def test_label_needs_something_to_add_or_remove(gh_repo):
    out = gh_repo.run("label", "#7")
    assert out.returncode == 2
    assert gh_repo.calls() == []


class FakeGitea:
    """Answers urlopen for a Gitea repo with label ids; records every request."""

    def __init__(self):
        self.labels = [{"id": 1, "name": "bug"}]
        self.issue = {"number": 7, "user": {"login": "giteauser"}, "labels": [{"id": 1, "name": "bug"}]}
        self.requests = []

    def __call__(self, req, timeout=None):
        method, url = req.get_method(), req.full_url
        body = json.loads(req.data) if req.data else None
        self.requests.append((method, url, body))
        path = url.split("/api/v1/repos/o/r", 1)[1]
        route, _, query = path.partition("?")
        if method == "GET" and route == "/labels":
            page = int(dict(q.split("=") for q in query.split("&")).get("page", "1"))
            result = self.labels if page == 1 else []
        elif method == "POST" and route == "/labels":
            label = {"id": max(l["id"] for l in self.labels) + 1, "name": body["name"]}
            self.labels.append(label)
            result = label
        elif method == "GET" and route == "/issues/7":
            result = self.issue
        elif method == "GET" and route == "/issues/7/labels":
            result = self.issue["labels"]
        elif method == "POST" and route == "/issues/7/labels":
            for lid in body["labels"]:
                label = next(l for l in self.labels if l["id"] == lid)
                if label not in self.issue["labels"]:
                    self.issue["labels"].append(label)
            result = self.issue["labels"]
        elif method == "DELETE" and route.startswith("/issues/7/labels/"):
            lid = int(route.rsplit("/", 1)[1])
            self.issue["labels"] = [l for l in self.issue["labels"] if l["id"] != lid]
            result = None
        else:
            raise AssertionError(f"unexpected {method} {url}")
        payload = b"" if result is None else json.dumps(result).encode()

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return payload
        return Resp()


@pytest.fixture
def gitea(monkeypatch):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    fake = FakeGitea()
    monkeypatch.setattr(tracker.urllib.request, "urlopen", fake)
    monkeypatch.setattr(tracker, "forge", lambda: tracker.Gitea("https://git.example.com", "o", "r"))
    return fake


def run_main(monkeypatch, capsys, *args):
    monkeypatch.setattr(tracker.sys, "argv", ["tracker.py", *args])
    code = tracker.main()
    return code, capsys.readouterr()


def test_gitea_label_add_creates_a_missing_label_then_lists_it(gitea, monkeypatch, capsys):
    code, _ = run_main(monkeypatch, capsys, "label", "#7", "--add", "factory:running")
    assert code == 0
    assert ("POST", "https://git.example.com/api/v1/repos/o/r/labels",
            {"name": "factory:running", "color": "#ededed"}) in gitea.requests
    assert ("POST", "https://git.example.com/api/v1/repos/o/r/issues/7/labels",
            {"labels": [2]}) in gitea.requests
    code, out = run_main(monkeypatch, capsys, "labels", "#7")
    assert code == 0
    assert out.out.splitlines() == ["bug", "factory:running"]


def test_gitea_label_remove_resolves_the_name_to_its_id(gitea, monkeypatch, capsys):
    code, _ = run_main(monkeypatch, capsys, "label", "7", "--remove", "bug", "missing")
    assert code == 0
    assert gitea.issue["labels"] == []
    deletes = [r for r in gitea.requests if r[0] == "DELETE"]
    assert [r[1] for r in deletes] == ["https://git.example.com/api/v1/repos/o/r/issues/7/labels/1"]
    assert not [r for r in gitea.requests if r[0] == "POST"]


def test_gitea_author_prints_the_opener_login(gitea, monkeypatch, capsys):
    code, out = run_main(monkeypatch, capsys, "author", "#7")
    assert code == 0
    assert out.out.strip() == "giteauser"


def test_protected_label_is_refused_before_any_gitea_call(gitea, monkeypatch, capsys):
    code, out = run_main(monkeypatch, capsys, "label", "#7", "--add", "factory:approved")
    assert code == 2
    assert "person" in out.err
    assert gitea.requests == []


# --- list ---------------------------------------------------------------------

def seed_github_issues(gh_repo):
    state = gh_repo.state()
    state["issues"] = {
        "7": {"title": "Epic: old", "labels": ["bug"], "author": "a", "createdAt": "2026-01-01T00:00:00Z"},
        "9": {"title": "Epic: new", "labels": [], "author": "a", "createdAt": "2026-03-01T00:00:00Z"},
        "8": {"title": "Fix a typo", "labels": ["bug"], "author": "a", "createdAt": "2026-02-01T00:00:00Z"},
        "6": {"title": "Epic: done", "labels": [], "author": "a", "state": "closed",
              "createdAt": "2025-12-01T00:00:00Z"},
    }
    Path(gh_repo.state_path).write_text(json.dumps(state))


def test_github_list_prints_open_issues_oldest_first(gh_repo):
    seed_github_issues(gh_repo)
    out = gh_repo.run("list")
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [
        {"number": 7, "title": "Epic: old", "labels": ["bug"], "created_at": "2026-01-01T00:00:00Z"},
        {"number": 8, "title": "Fix a typo", "labels": ["bug"], "created_at": "2026-02-01T00:00:00Z"},
        {"number": 9, "title": "Epic: new", "labels": [], "created_at": "2026-03-01T00:00:00Z"},
    ]
    call = gh_repo.calls()[0]
    assert call[:2] == ["issue", "list"]
    assert call[call.index("--json") + 1] == "number,title,labels,createdAt"
    assert call[call.index("--limit") + 1] == "1000"


def test_github_list_filters_by_state_label_and_title_prefix(gh_repo):
    seed_github_issues(gh_repo)
    out = gh_repo.run("list", "--state", "all", "--title-prefix", "Epic:")
    assert out.returncode == 0, out.stderr
    assert [i["number"] for i in json.loads(out.stdout)] == [6, 7, 9]
    out = gh_repo.run("list", "--label", "bug", "--title-prefix", "Epic:")
    assert out.returncode == 0, out.stderr
    assert [i["number"] for i in json.loads(out.stdout)] == [7]


def test_list_rejects_an_unknown_state(gh_repo):
    out = gh_repo.run("list", "--state", "merged")
    assert out.returncode == 2
    assert gh_repo.calls() == []


class FakeGiteaIssues:
    """Answers urlopen for Gitea's issue list, 2 per page; records every request."""

    def __init__(self, issues):
        self.issues = issues
        self.requests = []

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.requests.append((req.get_method(), url))
        route, _, query = url.split("/api/v1/repos/o/r", 1)[1].partition("?")
        assert route == "/issues", url
        q = dict(part.split("=", 1) for part in query.split("&"))
        assert q["type"] == "issues"
        rows = [i for i in self.issues if q["state"] == "all" or i["state"] == q["state"]]
        rows.sort(key=lambda i: i["created_at"], reverse=True)  # Gitea lists newest first
        limit, page = int(q["limit"]), int(q["page"])
        payload = json.dumps(rows[(page - 1) * limit:page * limit]).encode()

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return payload
        return Resp()


def gitea_issue(n, title, labels, created, state="open"):
    return {"number": n, "title": title, "state": state, "created_at": created,
            "labels": [{"id": i, "name": name} for i, name in enumerate(labels)], "user": {"login": "x"}}


def test_gitea_list_pages_through_every_issue_oldest_first(monkeypatch, capsys):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    fake = FakeGiteaIssues([
        gitea_issue(3, "Epic: c", [], "2026-03-01T00:00:00Z"),
        gitea_issue(1, "Epic: a", ["factory:running"], "2026-01-01T00:00:00Z"),
        gitea_issue(2, "Chore", [], "2026-02-01T00:00:00Z"),
        gitea_issue(4, "Epic: closed", [], "2025-12-01T00:00:00Z", state="closed"),
    ])
    monkeypatch.setattr(tracker.urllib.request, "urlopen", fake)
    monkeypatch.setattr(tracker, "forge", lambda: tracker.Gitea("https://git.example.com", "o", "r"))
    monkeypatch.setattr(tracker.Gitea, "PAGE", 2)
    code, out = run_main(monkeypatch, capsys, "list", "--title-prefix", "Epic:")
    assert code == 0
    assert json.loads(out.out) == [
        {"number": 1, "title": "Epic: a", "labels": ["factory:running"], "created_at": "2026-01-01T00:00:00Z"},
        {"number": 3, "title": "Epic: c", "labels": [], "created_at": "2026-03-01T00:00:00Z"},
    ]
    assert len(fake.requests) == 3  # two full pages, then an empty one
    assert all("state=open" in url for _, url in fake.requests)


def test_gitea_list_filters_by_label_and_state(monkeypatch, capsys):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    fake = FakeGiteaIssues([
        gitea_issue(1, "Epic: a", ["bug"], "2026-01-01T00:00:00Z"),
        gitea_issue(4, "Epic: b", ["bug"], "2025-12-01T00:00:00Z", state="closed"),
        gitea_issue(2, "Epic: c", [], "2026-02-01T00:00:00Z", state="closed"),
    ])
    monkeypatch.setattr(tracker.urllib.request, "urlopen", fake)
    monkeypatch.setattr(tracker, "forge", lambda: tracker.Gitea("https://git.example.com", "o", "r"))
    code, out = run_main(monkeypatch, capsys, "list", "--state", "closed", "--label", "bug")
    assert code == 0
    assert [i["number"] for i in json.loads(out.out)] == [4]
