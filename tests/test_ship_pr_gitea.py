"""ship-pr on Gitea, and the merge policy on both forges.

No network: a fake answers urllib for one Gitea repo (the tracker.py test
style), and the GitHub side is checked through the pure gate. Shapes follow
Gitea 28's REST API as recorded read-only from a live instance.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

from conftest import ROOT, load

SCRIPTS = "templates/_shared/skills/ship-pr/scripts"
forge = load(f"{SCRIPTS}/forge.py", "ship_pr_forge_test")
merge_pr = load(f"{SCRIPTS}/merge_pr.py", "ship_pr_merge_test")
watch = load(f"{SCRIPTS}/watch_pr.py", "ship_pr_watch_test")
tracker = load(".agents/scripts/tracker.py", "ship_pr_tracker_test")
plan = load(".agents/scripts/plan.py", "ship_pr_plan_test")

HEAD = "b" * 40
OLD = "a" * 40


def base_state() -> dict:
    return {
        "pull": {
            "number": 7, "html_url": "https://git.example.com/o/r/pulls/7", "state": "open",
            "merged": False, "draft": False, "mergeable": True, "title": "feat: x",
            "user": {"login": "worker-bot"}, "labels": [],
            "head": {"ref": "feat/x", "sha": HEAD}, "base": {"ref": "main", "sha": "c" * 40},
            "merge_base": "c" * 40, "merge_commit_sha": None,
        },
        "others": [  # a PR stacked on feat/x
            {"number": 8, "html_url": "https://git.example.com/o/r/pulls/8", "state": "open",
             "head": {"ref": "feat/y", "sha": "d" * 40}, "base": {"ref": "feat/x"}},
        ],
        "statuses": [
            {"context": "ci / check (pull_request)", "status": "success"},
            {"context": "ci / lint (pull_request)", "status": "success"},
        ],
        "protection": [{"rule_name": "Main", "enable_status_check": True,
                        "status_check_contexts": ["ci / check*"], "required_approvals": 0,
                        "block_on_outdated_branch": False, "dismiss_stale_approvals": True,
                        "priority": 1}],
        "reviews": [{"id": 1, "user": {"login": "ocr"}, "state": "COMMENT", "commit_id": HEAD,
                     "stale": False, "dismissed": False, "submitted_at": "2026-11-25T12:00:00Z"}],
        "review_comments": {1: []},
        "issue_comments": [],
        "commits": [{"sha": HEAD, "commit": {"committer": {"date": "2026-11-25T11:00:00Z"}}}],
        "files": [{"filename": "src/app.py"}],
        "me": "worker-bot",
        "has_reply_endpoint": True,
        "has_resolve_endpoint": True,
        "protection_status": 200,
    }


def finding(cid, body, *, who="ocr", path="src/app.py", pos=10, at="2026-11-25T12:00:01Z", resolver=None):
    return {"id": cid, "user": {"login": who}, "path": path, "position": pos, "original_position": 0,
            "body": body, "created_at": at, "resolver": resolver}


class FakeGitea:
    def __init__(self, state: dict):
        self.s = state
        self.requests: list[tuple[str, str, dict | None]] = []

    def __call__(self, req, timeout=None):
        method, url = req.get_method(), req.full_url
        body = json.loads(req.data) if req.data else None
        self.requests.append((method, url, body))
        assert req.headers.get("Authorization") == "token t"
        route, _, query = url.split("/api/v1", 1)[1].partition("?")
        q = dict(p.split("=", 1) for p in query.split("&") if p)
        page = int(q.get("page", "1"))
        s = self.s
        repo = route.removeprefix("/repos/o/r")

        def paged(items):
            return items if page == 1 else []

        if method == "GET" and route == "/user":
            result = {"login": s["me"]}
        elif method == "GET" and repo == "/pulls":
            pulls = [s["pull"], *s["others"]]
            if "base_branch" in q:
                pulls = [p for p in pulls if p["base"]["ref"] == q["base_branch"]]
            result = paged([p for p in pulls if p["state"] == "open"])
        elif method == "POST" and repo == "/pulls":
            result = {**s["pull"], "number": 9, "html_url": "https://git.example.com/o/r/pulls/9"}
        elif method == "GET" and repo == "/pulls/7":
            result = s["pull"]
        elif method == "PATCH" and repo.startswith("/pulls/"):
            result = {}
        elif method == "GET" and repo == f"/commits/{HEAD}/status":
            result = {"statuses": paged(s["statuses"]), "total_count": len(s["statuses"])}
        elif method == "GET" and repo == "/branch_protections":
            if s["protection_status"] != 200:
                raise urllib.error.HTTPError(url, s["protection_status"], "Forbidden", {}, None)
            result = s["protection"]
        elif method == "GET" and repo == "/pulls/7/reviews":
            result = paged(s["reviews"])
        elif method == "GET" and repo.startswith("/pulls/7/reviews/") and repo.endswith("/comments"):
            result = s["review_comments"][int(repo.split("/")[4])]
        elif method == "GET" and repo == "/issues/7/comments":
            result = s["issue_comments"]
        elif method == "POST" and repo == "/issues/7/comments":
            result = {"id": 900, "body": body["body"]}
        elif method == "GET" and repo == "/pulls/7/commits":
            result = paged(s["commits"])
        elif method == "GET" and repo == "/pulls/7/files":
            result = paged(s["files"])
        elif method == "POST" and repo.startswith("/pulls/7/comments/") and repo.endswith("/replies"):
            if not s["has_reply_endpoint"]:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            result = {"id": 901, "body": body["body"]}
        elif method == "POST" and repo.startswith("/pulls/comments/") and repo.endswith("/resolve"):
            if not s["has_resolve_endpoint"]:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            result = None
        elif method == "POST" and repo == "/pulls/7/merge":
            s["pull"] = {**s["pull"], "merged": True, "state": "closed", "merge_commit_sha": "e" * 40}
            result = None
        else:
            raise AssertionError(f"unexpected {method} {url}")
        payload = b"" if result is None else json.dumps(result).encode()

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return payload
        return Resp()

    def calls(self, method: str, fragment: str) -> list:
        return [r for r in self.requests if r[0] == method and fragment in r[1]]


@pytest.fixture
def gitea(monkeypatch):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    monkeypatch.delenv("TEA_TOKEN", raising=False)
    monkeypatch.delenv("GITEA_URL", raising=False)
    monkeypatch.delenv("SHIP_PR_REPLIERS", raising=False)
    fake = FakeGitea(base_state())
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    client = forge.Gitea(tracker.Gitea("https://git.example.com", "o", "r"), tracker.GiteaError)
    fake.client = client
    return fake


# ── detection ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(("remote", "want"), [
    ("git@github.com:o/r.git", "github"),
    ("https://github.com/o/r", "github"),
    ("https://git.example.com/o/r.git", "gitea"),
    ("ssh://git@git.example.com:2222/o/r.git", "gitea"),
])
def test_detects_the_forge_from_origin_like_tracker(monkeypatch, remote, want):
    monkeypatch.delenv("TRACKER", raising=False)
    monkeypatch.setattr(forge, "origin_url", lambda: remote)
    assert forge.detect() == want


def test_tracker_override_wins_and_a_bad_one_is_an_error(monkeypatch):
    monkeypatch.setattr(forge, "origin_url", lambda: "git@github.com:o/r.git")
    monkeypatch.setenv("TRACKER", "Gitea")
    assert forge.detect() == "gitea"
    monkeypatch.setenv("TRACKER", "gitlab")
    with pytest.raises(forge.ForgeError, match="TRACKER"):
        forge.detect()


def test_gitea_without_a_token_is_a_setup_error(monkeypatch):
    monkeypatch.delenv("TRACKER", raising=False)
    monkeypatch.delenv("GITEA_TOKEN", raising=False)
    monkeypatch.delenv("TEA_TOKEN", raising=False)
    monkeypatch.setattr(forge, "origin_url", lambda: "https://git.example.com/o/r.git")
    with pytest.raises(forge.ForgeError, match="GITEA_TOKEN"):
        forge.connect()


def test_gitea_url_overrides_the_remote_host(monkeypatch, gitea):
    monkeypatch.setenv("GITEA_URL", "https://gitea.internal:3000")
    monkeypatch.setattr(forge, "origin_url", lambda: "git@git.example.com:o/r.git")
    assert forge.connect().client.api == "https://gitea.internal:3000/api/v1/repos/o/r"


def test_tracker_request_raises_with_the_http_status(monkeypatch):
    monkeypatch.setenv("GITEA_TOKEN", "t")
    def missing(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
    monkeypatch.setattr(urllib.request, "urlopen", missing)
    client = tracker.Gitea("https://git.example.com", "o", "r")
    with pytest.raises(tracker.GiteaError) as caught:
        client.request("GET", "/pulls/1")
    assert caught.value.status == 404
    with pytest.raises(SystemExit, match="tracker: Gitea GET /pulls/1 -> 404"):
        client.call("GET", "/pulls/1")


# ── PR, checks, review state ──────────────────────────────────────────────


def test_find_and_create_the_pr_for_a_branch(gitea):
    assert gitea.client.find("feat/x") == {"number": 7, "url": "https://git.example.com/o/r/pulls/7",
                                           "state": "OPEN"}
    assert gitea.client.find("nope") is None
    made = gitea.client.create("feat: x", "body", "main", "feat/x")
    assert made["number"] == 9
    assert gitea.calls("POST", "/pulls")[-1][2] == {"title": "feat: x", "body": "body", "base": "main",
                                                    "head": "feat/x"}


def test_required_checks_come_from_branch_protection_globs(gitea):
    gitea.s["statuses"][1]["status"] = "failure"  # lint is not required
    assert gitea.client.checks(7, required=True) == [{"name": "ci / check (pull_request)", "bucket": "pass"}]
    assert {c["bucket"] for c in gitea.client.checks(7)} == {"pass", "fail"}


def test_a_required_context_not_reported_yet_is_pending(gitea):
    gitea.s["protection"][0]["status_check_contexts"] = ["ci / check*", "security"]
    rows = gitea.client.checks(7, required=True)
    assert {"name": "security", "bucket": "pending"} in rows


def test_unreadable_protection_requires_every_status(gitea):
    gitea.s["protection_status"] = 403
    gitea.s["statuses"][1]["status"] = "error"
    assert {c["bucket"] for c in gitea.client.checks(7, required=True)} == {"pass", "fail"}


def test_latest_reject_per_reviewer_is_changes_requested(gitea):
    gitea.s["reviews"] = [
        {"id": 1, "user": {"login": "amy"}, "state": "APPROVED", "commit_id": HEAD, "submitted_at": "2026-01-01T01:00:00Z"},
        {"id": 2, "user": {"login": "bob"}, "state": "REQUEST_CHANGES", "commit_id": HEAD, "submitted_at": "2026-01-01T02:00:00Z"},
        {"id": 3, "user": {"login": "bob"}, "state": "COMMENT", "commit_id": HEAD, "submitted_at": "2026-01-01T03:00:00Z"},
    ]
    gitea.s["review_comments"] = {1: [], 2: [], 3: []}
    assert gitea.client.view(7)["changes_requested"]
    gitea.s["reviews"].append({"id": 4, "user": {"login": "bob"}, "state": "APPROVED", "commit_id": HEAD,
                               "submitted_at": "2026-01-01T04:00:00Z"})
    assert not gitea.client.view(7)["changes_requested"]


def test_conflicts_and_outdated_branches_are_not_clean(gitea):
    gitea.s["pull"]["mergeable"] = False
    assert gitea.client.view(7)["merge_state"] == "DIRTY"
    gitea.s["pull"]["mergeable"] = True
    gitea.s["pull"]["merge_base"] = "f" * 40
    assert gitea.client.view(7)["merge_state"] == "CLEAN"  # behind, but protection allows it
    gitea.s["protection"][0]["block_on_outdated_branch"] = True
    assert gitea.client.view(7)["merge_state"] == "BEHIND"


@pytest.mark.parametrize(("change", "want"), [
    (lambda s: None, 0),
    (lambda s: s["statuses"][0].update(status="failure"), 10),
    (lambda s: s["statuses"][0].update(status="pending"), None),
    (lambda s: s["reviews"].append({"id": 2, "user": {"login": "amy"}, "state": "REQUEST_CHANGES",
                                     "commit_id": HEAD, "submitted_at": "2026-11-25T12:30:00Z"}), 20),
    (lambda s: s["reviews"][0].update(submitted_at="2026-11-25T10:00:00Z"), None),  # review predates the head
    (lambda s: s["pull"].update(merged=True, state="closed"), 50),
])
def test_watcher_judges_gitea_like_github(gitea, change, want):
    gitea.s["review_comments"][2] = []
    change(gitea.s)
    pr, checks = gitea.client.gh_view(7)
    code, _status, _message = watch.evaluate(pr, checks, ("ocr",))
    assert code == want


# ── findings ──────────────────────────────────────────────────────────────


def answered_by(gitea) -> dict:
    return {t["id"]: t["answered_by"] for t in gitea.client.threads(7)}


def test_an_unanswered_finding_is_open_and_keeps_its_severity(gitea):
    gitea.s["review_comments"][1] = [finding(11, "Important — leaks a handle"), finding(12, "Nit — name", pos=20)]
    threads = {t["id"]: t for t in gitea.client.threads(7)}
    assert threads[11]["answered"] is False and threads[11]["severity"] == "important"
    assert threads[12]["severity"] == "nit"


def test_a_thread_reply_from_the_pr_author_answers_it(gitea):
    gitea.s["review_comments"][1] = [finding(11, "Important — x"),
                                     finding(13, "Fixed in abc", who="worker-bot", at="2026-11-25T12:05:00Z")]
    assert answered_by(gitea) == {11: "replied"}


def test_the_reviewer_talking_to_itself_does_not_answer_it(gitea):
    gitea.s["me"] = "ocr"  # the token's user is also the reviewer
    gitea.s["review_comments"][1] = [finding(11, "Important — x"),
                                     finding(13, "also this", who="ocr", at="2026-11-25T12:05:00Z")]
    assert answered_by(gitea) == {11: None}


def test_a_pr_comment_naming_the_finding_answers_it(gitea):
    gitea.s["review_comments"][1] = [finding(11, "Important — x"), finding(12, "Important — y", pos=20)]
    gitea.s["issue_comments"] = [{"id": 50, "user": {"login": "worker-bot"}, "body": "Re inline #11: by design",
                                  "created_at": "2026-11-25T12:06:00Z"}]
    assert answered_by(gitea) == {11: "replied", 12: None}


def test_a_comment_from_someone_else_does_not_answer_it(gitea):
    gitea.s["review_comments"][1] = [finding(11, "Important — x")]
    gitea.s["issue_comments"] = [{"id": 50, "user": {"login": "passer-by"}, "body": "comment 11 is wrong",
                                  "created_at": "2026-11-25T12:06:00Z"}]
    assert answered_by(gitea) == {11: None}


def test_a_commit_after_the_review_answers_it(gitea):
    gitea.s["reviews"][0].update(commit_id=OLD, stale=True)
    gitea.s["review_comments"][1] = [finding(11, "Important — x")]
    assert answered_by(gitea) == {11: "commit"}


def test_a_resolved_finding_is_answered(gitea):
    gitea.s["review_comments"][1] = [finding(11, "Important — x", resolver={"login": "worker-bot"})]
    assert answered_by(gitea) == {11: "resolved"}


def test_reply_uses_the_thread_and_marks_the_finding(gitea):
    made = gitea.client.reply(7, 11, "Fixed in abc123")
    assert made["via"] == "thread"
    sent = gitea.calls("POST", "/pulls/7/comments/11/replies")[0][2]["body"]
    assert "Fixed in abc123" in sent and "<!-- ship-pr:reply 11 -->" in sent


def test_reply_falls_back_to_a_pr_comment_without_the_endpoint(gitea):
    gitea.s["has_reply_endpoint"] = False
    made = gitea.client.reply(7, 11, "Not a bug: see L40")
    assert made["via"] == "comment"
    body = gitea.calls("POST", "/issues/7/comments")[0][2]["body"]
    assert forge.references(body, 11)
    # and the fallback reply is then recognised as an answer
    gitea.s["review_comments"][1] = [finding(11, "Important — x")]
    gitea.s["issue_comments"] = [{"id": 900, "user": {"login": "worker-bot"}, "body": body,
                                  "created_at": "2026-11-25T12:06:00Z"}]
    assert answered_by(gitea) == {11: "replied"}


def test_resolve_is_skipped_where_the_server_cannot(gitea):
    assert gitea.client.resolve(11) is True
    gitea.s["has_resolve_endpoint"] = False
    assert gitea.client.resolve(11) is False


# ── policy ────────────────────────────────────────────────────────────────


def write_policy(root, policy) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 2}
    if policy is not None:
        manifest["merge_policy"] = policy
    (root / ".claude" / "harness.json").write_text(json.dumps(manifest))


def test_no_policy_means_the_defaults(tmp_path):
    assert merge_pr.load_policy(tmp_path) == merge_pr.DEFAULT_POLICY
    write_policy(tmp_path, None)
    assert merge_pr.load_policy(tmp_path) == merge_pr.DEFAULT_POLICY
    write_policy(tmp_path, {"merge": "never"})
    assert merge_pr.load_policy(tmp_path) == {**merge_pr.DEFAULT_POLICY, "merge": "never"}


@pytest.mark.parametrize("policy", [
    {"merge": "always"}, {"method": "fast-forward"}, {"irreversible": "auto"},
    {"irreversible_paths": "db/**"}, {"mergee": "never"}, ["never"],
])
def test_an_invalid_policy_is_refused_not_guessed(tmp_path, policy):
    write_policy(tmp_path, policy)
    with pytest.raises(merge_pr.PolicyError):
        merge_pr.load_policy(tmp_path)


def test_irreversible_globs_are_plan_pys():
    assert merge_pr.irreversible_globs() == list(plan.IRREVERSIBLE_GLOBS)


@pytest.mark.parametrize("path", [
    "migrations/0001.py", "app/migrations/0001.py", "alembic/env.py", "schema.sql", "db/x/seed.sql",
    "deploy/prod.yaml", "infra/main.tf", "modules/vpc/main.tf", "k8s/app.yaml", "helm/chart/values.yaml",
    "src/app.py", "docs/deploy.md", "src/migrations.py", "deployer/x", "README.sql.md",
])
def test_glob_matching_agrees_with_plan_py(path):
    globs = list(plan.IRREVERSIBLE_GLOBS)
    assert bool(merge_pr.irreversible([path], globs)) == plan.covered_by(path, globs)


# ── the merge gate end to end (Gitea) ─────────────────────────────────────


@pytest.fixture
def run_merge(gitea, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)  # no workflow files: an empty check list would settle
    monkeypatch.setattr(merge_pr, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(merge_pr.forge, "connect", lambda: gitea.client)

    def run(*args, policy=None):
        write_policy(tmp_path, policy)
        monkeypatch.setattr(sys, "argv", ["merge_pr.py", "7", *args])
        code = merge_pr.main()
        return code, json.loads(capsys.readouterr().out)
    return run


def test_merges_with_the_policy_method_after_retargeting_dependents(gitea, run_merge):
    code, report = run_merge(policy={"method": "squash"})
    assert code == 0 and report["decision"] == "merged"
    assert report["merge_commit"] == "e" * 40 and report["retargeted"] == [8]
    assert gitea.calls("PATCH", "/pulls/8")[0][2] == {"base": "main"}
    assert gitea.calls("POST", "/pulls/7/merge")[0][2] == {
        "Do": "squash", "head_commit_id": HEAD, "delete_branch_after_merge": True}
    patch_at = gitea.requests.index(gitea.calls("PATCH", "/pulls/8")[0])
    assert patch_at < gitea.requests.index(gitea.calls("POST", "/pulls/7/merge")[0])


def test_policy_never_stops_at_ready(gitea, run_merge):
    code, report = run_merge(policy={"merge": "never"})
    assert code == 3 and report["decision"] == "ready"
    assert not gitea.calls("POST", "/merge") and not gitea.calls("PATCH", "/pulls/")


def test_an_irreversible_path_always_needs_a_person(gitea, run_merge):
    gitea.s["files"].append({"filename": "app/migrations/0002_add.py"})
    code, report = run_merge()
    assert code == 3 and report["irreversible_paths"] == ["app/migrations/0002_add.py"]
    assert not gitea.calls("POST", "/merge")


def test_policy_paths_extend_the_irreversible_lane(gitea, run_merge):
    gitea.s["files"] = [{"filename": "db/schema.prisma"}]
    code, _ = run_merge(policy={"irreversible_paths": ["db/**"]})
    assert code == 3


@pytest.mark.parametrize(("change", "reason"), [
    (lambda s: s["statuses"][0].update(status="failure"), "checks not green"),
    (lambda s: s["reviews"].append({"id": 2, "user": {"login": "amy"}, "state": "REQUEST_CHANGES",
                                     "commit_id": HEAD, "submitted_at": "2026-11-25T12:30:00Z"}),
     "requested changes"),
    (lambda s: s["review_comments"].__setitem__(1, [finding(11, "Important — leak")]), "not fixed or answered"),
    (lambda s: s["review_comments"].__setitem__(1, [finding(11, "this looks off")]), "not fixed or answered"),
    (lambda s: s["pull"].update(mergeable=False), "merge state is dirty"),
    (lambda s: s["pull"].update(labels=[{"name": "do-not-merge"}]), "do-not-merge"),
    (lambda s: s["pull"].update(draft=True), "draft"),
])
def test_an_unmet_gate_blocks_the_merge(gitea, run_merge, change, reason):
    gitea.s["review_comments"][2] = []
    change(gitea.s)
    code, report = run_merge()
    assert code == 1 and report["decision"] == "blocked"
    assert any(reason in r for r in report["blocked_by"]), report["blocked_by"]
    assert not gitea.calls("POST", "/merge")


def test_an_open_nit_does_not_block_on_gitea(gitea, run_merge):
    gitea.s["review_comments"][1] = [finding(11, "Nit — rename")]
    code, report = run_merge("--dry-run")
    assert code == 0 and report["decision"] == "would-merge" and report["open_findings"] == 1
    assert not gitea.calls("POST", "/merge")


def test_an_invalid_policy_merges_nothing(gitea, run_merge):
    code, report = run_merge(policy={"merge": "yes"})
    assert code == 2 and "merge_policy" in report["error"]
    assert not gitea.requests


# ── GitHub keeps its rule ─────────────────────────────────────────────────


def gh_view(**over):
    return {"state": "OPEN", "draft": False, "labels": [], "merge_state": "CLEAN",
            "changes_requested": False, **over}


def test_github_still_blocks_on_any_unresolved_thread():
    nit = [{"path": "a.py", "line": 1, "severity": "nit", "answered": False}]
    assert merge_pr.gate(gh_view(), [{"name": "ci", "bucket": "pass"}], nit, True, "github")
    assert not merge_pr.gate(gh_view(), [{"name": "ci", "bucket": "pass"}], nit, True, "gitea")


def test_empty_checks_block_only_where_ci_exists():
    assert merge_pr.gate(gh_view(), [], [], True, "github")
    assert not merge_pr.gate(gh_view(), [], [], False, "github")


def test_github_requires_a_clean_merge_state():
    assert merge_pr.gate(gh_view(merge_state="UNSTABLE"), [{"name": "ci", "bucket": "pass"}], [], True, "github")


# ── render keeps the repo's policy ────────────────────────────────────────


def test_render_writes_the_default_policy_and_keeps_an_edited_one(tmp_path):
    def render():
        subprocess.run([sys.executable, str(ROOT / "templates/scripts/render.py"), "--output-dir", str(tmp_path),
                        "--project-name", "Policy", "--stacks", "python"], check=True, capture_output=True)
    render()
    path = tmp_path / ".claude" / "harness.json"
    manifest = json.loads(path.read_text())
    assert manifest["merge_policy"] == merge_pr.DEFAULT_POLICY
    manifest["merge_policy"] = {"merge": "never", "method": "squash"}
    path.write_text(json.dumps(manifest))
    render()
    assert json.loads(path.read_text())["merge_policy"] == {"merge": "never", "method": "squash"}



# ── GitHub through a fake gh: same output, same calls ────────────────────

FAKE_GH = r'''#!{python}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
if args[:2] == ["repo", "view"]:
    print("o/r")
elif args[:2] == ["api", "graphql"] and any("reviewThreads" in a for a in args):
    node = lambda i, resolved, outdated, body: {{"id": i, "isResolved": resolved, "isOutdated": outdated,
        "path": "a.py", "line": 3, "first": {{"nodes": [{{"author": {{"login": "rev[bot]"}}, "body": body}}]}},
        "latest": {{"nodes": [{{"author": {{"login": "rev[bot]"}}, "body": body}}]}}}}
    print(json.dumps({{"data": {{"repository": {{"pullRequest": {{"reviewThreads": {{
        "pageInfo": {{"hasNextPage": False, "endCursor": None}}, "nodes": [
        node("T1", False, False, "Important — leak"), node("T2", True, False, "Nit — x"),
        node("T3", False, True, "Nit — y")]}}}}}}}}}}))
elif args[:2] == ["api", "graphql"]:
    print("{{}}")
else:
    sys.exit(f"fake gh: unexpected {{args}}")
'''


@pytest.fixture
def gh_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:o/r.git"], cwd=repo, check=True)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "gh").write_text(FAKE_GH.format(python=sys.executable))
    (bindir / "gh").chmod(0o755)
    log = tmp_path / "gh.log"
    log.write_text("")
    env = {k: v for k, v in __import__("os").environ.items() if k not in ("TRACKER", "GITEA_TOKEN")}
    env.update(PATH=f"{bindir}:{env.get('PATH', '')}", FAKE_GH_LOG=str(log))

    def run(*args):
        out = subprocess.run([sys.executable, str(ROOT / SCRIPTS / "pr_threads.py"), *args], cwd=repo,
                             env=env, capture_output=True, text=True)
        return out, [json.loads(line) for line in log.read_text().splitlines()]
    return run


def test_github_threads_list_is_unchanged(gh_repo):
    out, _calls = gh_repo("--pr", "5")
    assert out.returncode == 0
    assert out.stdout == "T1\ta.py:3\trev[bot]\tImportant — leak\n"
    assert out.stderr == "unresolved=1\n"


def test_github_reply_and_resolve_send_the_graphql_mutations(gh_repo):
    out, calls = gh_repo("--pr", "5", "--reply", "T1", "--body", "Fixed in abc", "--resolve")
    assert out.returncode == 0, out.stderr
    reply, resolve = calls
    assert any("addPullRequestReviewThreadReply" in a for a in reply)
    assert "thread=T1" in reply and "body=Fixed in abc" in reply
    assert any("resolveReviewThread" in a for a in resolve) and "thread=T1" in resolve


def test_finds_the_user_level_tracker_when_the_repo_has_none(tmp_path, monkeypatch):
    # A repo that takes the pipeline from the user-level install has no
    # .agents/scripts/tracker.py; ship-pr must use ~/.agents/scripts/tracker.py.
    skill = tmp_path / "repo" / ".agents" / "skills" / "ship-pr" / "scripts"
    skill.mkdir(parents=True)
    home = tmp_path / "home"
    (home / ".agents" / "scripts").mkdir(parents=True)
    (home / ".agents" / "scripts" / "tracker.py").write_text("WHERE = 'user'\n")
    monkeypatch.setattr(forge.Path, "home", classmethod(lambda cls: home))
    found = forge.tracker_module(skill / "forge.py")
    assert found is not None and found.WHERE == "user"


def test_a_non_github_origin_without_tracker_is_an_error_not_github(monkeypatch):
    monkeypatch.delenv("TRACKER", raising=False)
    monkeypatch.setattr(forge, "tracker_module", lambda *a: None)
    monkeypatch.setattr(forge, "origin_url", lambda: "https://git.example.com/o/r.git")
    with pytest.raises(forge.ForgeError, match="tracker.py"):
        forge.detect()
    monkeypatch.setattr(forge, "origin_url", lambda: "git@github.com:o/r.git")
    assert forge.detect() == "github"


def test_github_threads_follow_every_page_and_report_the_latest_comment(monkeypatch):
    # The merge gate treats this list as complete: a thread past the first page,
    # or a reply past the first few comments, must not disappear.
    def node(i, latest):
        return {"id": i, "isResolved": False, "isOutdated": False, "path": "a.py", "line": 1,
                "first": {"nodes": [{"author": {"login": "rev"}, "body": "Important — x"}]},
                "latest": {"nodes": [{"author": {"login": latest}, "body": f"{latest} said"}]}}
    pages = {None: ([node("T1", "rev")], True, "c1"), "c1": ([node("T2", "me")], False, "c2")}
    seen = []

    def fake_json(*args, check=True):
        cursor = next((a.split("=", 1)[1] for a in args if a.startswith("cursor=")), None)
        seen.append(cursor)
        nodes, more, end = pages[cursor]
        return {"data": {"repository": {"pullRequest": {"reviewThreads": {
            "pageInfo": {"hasNextPage": more, "endCursor": end}, "nodes": nodes}}}}}

    gh = forge.GitHub()
    monkeypatch.setattr(gh, "repo", lambda: ("o", "r"))
    monkeypatch.setattr(gh, "json", fake_json)
    threads = gh.threads("5")
    assert [t["id"] for t in threads] == ["T1", "T2"]
    assert seen == [None, "c1"]
    assert threads[1]["author"] == "me" and threads[1]["severity"] == "important"
    assert "comments(first: 1)" in forge.THREADS_QUERY and "comments(last: 1)" in forge.THREADS_QUERY
