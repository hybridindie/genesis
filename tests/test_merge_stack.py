"""merge_stack.py: a reviewed stack merges bottom-up without rebases.

No network: a fake forge holds the PRs, and fakes stand in for git's fetch
and the landed-file check.
"""

from __future__ import annotations

import pytest

from conftest import load

SCRIPTS = "templates/_shared/skills/ship-pr/scripts"
stack = load(f"{SCRIPTS}/merge_stack.py", "ship_pr_merge_stack_test")

POLICY = {"merge": "when-green", "method": "squash", "irreversible": "person", "irreversible_paths": []}


def view(n: int, base: str) -> dict:
    return {"number": n, "url": f"https://x/{n}", "state": "OPEN", "draft": False, "head": f"part-{n}",
            "sha": f"{n:040d}", "base": base, "author": "bot", "labels": [], "changes_requested": False,
            "merge_state": "CLEAN"}


class Fake:
    kind = "github"

    def __init__(self, views, checks=None, threads=None, files=None):
        self.views = {v["number"]: dict(v) for v in views}
        self.checks_ = checks or {}
        self.threads_ = threads or {}
        self.files_ = files or {}
        self.calls: list[tuple] = []

    def view(self, n):
        return dict(self.views[int(n)])

    def checks(self, n, required=False):
        return self.checks_.get(int(n), [{"name": "ci", "bucket": "pass"}])

    def threads(self, n):
        return self.threads_.get(int(n), [])

    def files(self, n):
        return self.files_.get(int(n), [f"src/{n}.py"])

    def dependents(self, head):
        return [n for n, v in self.views.items() if v["base"] == head and v["state"] == "OPEN"]

    def retarget(self, n, base):
        self.calls.append(("retarget", n, base))
        self.views[n]["base"] = base

    def merge(self, n, method, sha):
        self.calls.append(("merge", int(n), method, sha))
        self.views[int(n)]["state"] = "MERGED"
        return f"m{n}"


def three():
    return [view(1, "main"), view(2, "part-1"), view(3, "part-2")]


def runner(client, policy=POLICY, globs=(), *, off=None, heads=None):
    heads = heads or {}

    def fetch(ref):
        return heads.get(ref, client.views[int(ref.split("-")[1])]["sha"]) if ref != "main" else "landed"

    return stack.Stack(client, policy, list(globs), True, fetch=fetch,
                       differing=lambda tested, landed, files: (off or {}).get(tested, []),
                       sleep=lambda s: None, now=iter(range(0, 10**6, 10)).__next__)


def test_a_clean_stack_merges_bottom_up_retargeting_each_part_first():
    client = Fake(three())
    code, report = runner(client).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_MERGED, report
    assert [m["pr"] for m in report["merged"]] == [1, 2, 3]
    merges = [c for c in client.calls if c[0] == "merge"]
    assert [c[1] for c in merges] == [1, 2, 3]
    assert all(c[2] == "merge" for c in merges)  # the policy says squash
    # Each dependant moved to main before the branch it was based on went away.
    assert client.calls.index(("retarget", 2, "main")) < client.calls.index(merges[0])
    assert client.calls.index(("retarget", 3, "main")) < client.calls.index(merges[1])


def test_a_setup_error_merges_nothing():
    views = [view(1, "main"), view(2, "main")]
    client = Fake(views)
    code, report = runner(client, POLICY).run(["1", "2"], dry_run=False)
    assert code == stack.EXIT_SETUP and "targets main" in report["error"]
    assert not client.calls


@pytest.mark.parametrize("method", ["squash", "rebase", "merge"])
def test_every_policy_method_lands_a_stack_with_merge_commits(method):
    # A squash or rebase drops the commits the next part is based on, so it
    # would conflict wherever that part edits the lower part's lines.
    client = Fake(three())
    code, report = runner(client, {**POLICY, "method": method}).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_MERGED and report["method"] == "merge"
    assert {c[2] for c in client.calls if c[0] == "merge"} == {"merge"}


@pytest.mark.parametrize("fake, globs, code, at", [
    (dict(checks={3: [{"name": "ci", "bucket": "fail"}]}), (), stack.EXIT_BLOCKED, 3),
    (dict(threads={2: [{"answered": False, "severity": "nit", "path": "a.py", "line": 3}]}), (),
     stack.EXIT_BLOCKED, 2),
    (dict(files={2: ["migrations/0001.sql"]}), ("migrations/**",), stack.EXIT_PERSON, 2),
], ids=["red-ci", "open-thread", "irreversible"])
def test_one_failing_part_anywhere_merges_nothing(fake, globs, code, at):
    client = Fake(three(), **fake)
    got, report = runner(client, globs=globs).run(["1", "2", "3"], dry_run=False)
    assert (got, report["stopped_at"], report["merged"]) == (code, at, [])
    assert not client.calls


def test_dry_run_gates_everything_and_merges_nothing():
    client = Fake(three())
    code, report = runner(client).run(["1", "2", "3"], dry_run=True)
    assert code == stack.EXIT_MERGED and report["decision"] == "would-merge"
    assert not client.calls


def test_a_head_pushed_after_the_gate_stops_before_merging_it():
    client = Fake(three())
    code, report = runner(client, heads={"part-2": "f" * 40}).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_BLOCKED and report["stopped_at"] == 2
    assert [m["pr"] for m in report["merged"]] == [1]
    assert "head moved" in report["blocked_by"][0]


def test_a_part_never_retargeted_stops_the_stack():
    client = Fake(three())
    client.dependents = lambda head: []  # nothing moves part 2
    code, report = runner(client).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_BLOCKED and report["stopped_at"] == 2
    assert "not retargeted" in report["blocked_by"][0]


def test_a_landed_tree_that_differs_from_the_tested_head_stops_the_stack():
    client = Fake(three())
    code, report = runner(client, off={f"{2:040d}": ["src/2.py"]}).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_BLOCKED and report["stopped_at"] == 2
    assert [m["pr"] for m in report["merged"]] == [1, 2]
    assert "src/2.py" in report["blocked_by"][0]
    assert ("merge", 3, "merge", f"{3:040d}") not in client.calls


def test_a_part_the_forge_wont_merge_after_retarget_stops():
    client = Fake(three())
    real = client.retarget
    client.retarget = lambda n, base: (real(n, base), client.views[n].update(merge_state="DIRTY"))
    code, report = runner(client).run(["1", "2", "3"], dry_run=False)
    assert (code, report["stopped_at"], [m["pr"] for m in report["merged"]]) == (stack.EXIT_BLOCKED, 2, [1])


def test_a_retargeted_part_listing_no_checks_keeps_the_checks_its_head_passed():
    client = Fake(three())
    real = client.retarget

    def retarget(n, base):
        real(n, base)
        client.checks_[n] = []  # a base edit fires no pull_request run

    client.retarget = retarget
    code, report = runner(client).run(["1", "2", "3"], dry_run=False)
    assert code == stack.EXIT_MERGED, report
    assert [m["pr"] for m in report["merged"]] == [1, 2, 3]


def test_a_failed_check_after_a_merge_still_lists_the_part_as_merged():
    client = Fake(three())
    run = runner(client)
    real = run.fetch

    def fetch(ref):
        if ref == "main" and client.views[1]["state"] == "MERGED":
            raise stack.forge.ForgeError("git fetch origin main: timed out")
        return real(ref)

    run.fetch = fetch
    code, report = run.run(["1", "2", "3"], dry_run=False)
    assert (code, report["stopped_at"], [m["pr"] for m in report["merged"]]) == (stack.EXIT_BLOCKED, 1, [1])
    assert "landed" in report["blocked_by"][0]
