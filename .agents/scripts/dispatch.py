#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""The mechanical half of wave-dispatcher: git, plans and status, no judgment.

  dispatch.py load (--epic REF | --story REF... | --files FILE...) [--base REF]
  dispatch.py prepare [--max N] [--plan] [--allow-dirty] [--baseline-timeout S]
  dispatch.py check UNIT [--timeout SEC]
  dispatch.py merge UNIT
  dispatch.py block UNIT --note TEXT
  dispatch.py integrate STORY [--push]
  dispatch.py report

UNIT is `<story>/<track>` (e.g. S1/A). Every command prints JSON on stdout and
exits 0 on success, 1 when the unit failed a check (the JSON says why), 2 on a
usage or environment error.

State lives in `<git common dir>/agent-plan/`: a copy of each plan body, a
brief per prepared unit, and state.json recording where each body came from.
Every status change is written back to its source — the GitHub/Gitea issue via
tracker.py, or the original file for `--files`.

Trust: `check` and `integrate` run each plan's verify commands with `bash -c`
in the worktree. A plan loaded from an issue can be changed by anyone with
write access to that issue, so load only from trackers whose writers you
trust, and read new or changed verify commands before dispatching.

Layout, for a story whose plan says `branch: feat/41-x`:
  feat/41-x                    the story's integration branch (from the base, plus
                               the branches of the stories it depends on)
  feat/41-x--<track>           one branch per track
  <repo>-tracks/S1-integration and <repo>-tracks/S1-<track>   their worktrees
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

try:
    import yaml  # noqa: F401  (plan.py needs it; re-run this script, not plan.py, under uv)
except ImportError:
    if shutil.which("uv") and not os.environ.get("AGENT_PLAN_REEXEC"):
        os.environ["AGENT_PLAN_REEXEC"] = "1"
        os.execvp("uv", ["uv", "run", "--quiet", "--script", __file__, *sys.argv[1:]])
    sys.exit("dispatch.py needs PyYAML: install it, or install uv so it can fetch it")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


plan = _load("plan")


class DispatchError(Exception):
    pass


# ── git ──────────────────────────────────────────────────────────────────────

def git(*args: str, cwd: Path | str | None = None, check: bool = True) -> str:
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and run.returncode != 0:
        raise DispatchError(f"git {' '.join(args)}: {run.stderr.strip() or run.stdout.strip()}")
    return run.stdout.strip()


def ok(*args: str, cwd: Path | str | None = None) -> bool:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True).returncode == 0


def repo_root() -> Path:
    return Path(git("rev-parse", "--show-toplevel"))


def work_dir() -> Path:
    common = Path(git("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = (Path.cwd() / common).resolve()
    return common / "agent-plan"


def default_base() -> str:
    head = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    if head:
        return head
    for name in ("main", "master"):
        if ok("show-ref", "--verify", "--quiet", f"refs/heads/{name}"):
            return name
    return git("rev-parse", "--abbrev-ref", "HEAD")


# ── state ────────────────────────────────────────────────────────────────────

class State:
    def __init__(self) -> None:
        self.root = repo_root()
        self.work = work_dir()
        self.path = self.work / "state.json"
        try:
            self.data = json.loads(self.path.read_text()) if self.path.is_file() else {}
        except json.JSONDecodeError as exc:
            raise DispatchError(f"{self.path} is corrupt ({exc}); run dispatch.py load again") from exc

    def save(self) -> None:
        self.work.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n")

    @property
    def trees(self) -> Path:
        return Path(self.data.get("trees") or self.root.parent / f"{self.root.name}-tracks")

    @property
    def base(self) -> str:
        return self.data.get("base") or default_base()

    def files(self) -> list[str]:
        return [str(self.work / f) for f in sorted(self.data.get("sources", {}))]

    def plans(self):
        if not self.data.get("sources"):
            raise DispatchError("nothing loaded; run dispatch.py load first")
        return plan.load(self.files())

    def story_file(self, sid: str) -> Path:
        name = f"story-{sid}.md"
        if name not in self.data.get("sources", {}):
            raise DispatchError(f"story {sid} is not loaded")
        return self.work / name

    def story(self, sid: str) -> dict:
        return plan.extract(self.story_file(sid).read_text(encoding="utf-8"), f"story {sid}")

    def publish(self, name: str) -> None:
        """Write a body back where it came from."""
        src = self.data["sources"][name]
        body = self.work / name
        if src["kind"] == "file":
            shutil.copyfile(body, src["path"])
        elif src["kind"] == "tracker":
            tracker = _load("tracker")
            tracker.forge().put(tracker.number(src["ref"]), body.read_text(encoding="utf-8"))

    def set_status(self, sid: str, track: str, status: str, note: str | None = None) -> None:
        f = self.story_file(sid)
        f.write_text(plan.set_status(f.read_text(encoding="utf-8"), track, status, note), encoding="utf-8")
        self.publish(f.name)


def split_unit(unit: str) -> tuple[str, str]:
    if "/" not in unit:
        raise DispatchError(f"unit must be <story>/<track>, got {unit!r}")
    sid, track = unit.split("/", 1)
    return sid, track


def track_of(story: dict, track: str) -> dict:
    t = next((x for x in plan.as_list(story.get("tracks")) if str(x.get("id")) == track), None)
    if t is None:
        raise DispatchError(f"story {plan.story_key(story)} has no track {track}")
    return t


def story_branch(story: dict) -> str:
    branch = story.get("branch")
    if not branch or "<" in str(branch):
        raise DispatchError(f"story {plan.story_key(story)} has no branch in its plan")
    return str(branch)


def run_shell(command: str, cwd: Path, timeout: int) -> tuple[bool, str]:
    """Run a verify command. On timeout the whole process group is killed, so
    nothing it started keeps writing into the worktree after the cleanup."""
    proc = subprocess.Popen(["bash", "-c", command], cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        return False, f"timed out after {timeout}s"
    tail = "\n".join((out or "").strip().splitlines()[-30:])
    return proc.returncode == 0, tail


TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]*$|_test\.[^/]+$|\.(test|spec)\.[^/]+$")

WEAK_BRIEF = """

## Your check already passes
`{verify}` passes before you have changed anything, so on its own it cannot
show that your work is right. Write a failing test for the acceptance
criteria first (red), then make it pass (green). `check` rejects this track
if the diff adds or changes no test file.
"""


def baseline(st: "State", unit: str, verify: str, tree: Path, timeout: int) -> bool:
    """Whether `verify` already passes on the untouched worktree, run once per unit."""
    seen = st.data.setdefault("baselines", {})
    if unit not in seen:
        passed, _ = run_shell(verify, tree, timeout)
        restore(tree)
        seen[unit] = passed
        st.save()
    return bool(seen[unit])


def weak_check(st: "State", unit: str, t: dict) -> bool:
    """A verify that passed before any work, on a track that isn't a declared refactor."""
    return bool(st.data.get("baselines", {}).get(unit)) and t.get("verify_baseline") != "pass"


def clean_tree(cwd: Path) -> list[str]:
    return [line[3:] for line in git("status", "--porcelain", cwd=cwd).splitlines() if line.strip()]


def restore(cwd: Path) -> None:
    """Undo what a verify run wrote (caches, regenerated lockfiles) so the
    worktree shows only the agent's commits. Only called on a tree that was
    clean before the run, so nothing of the agent's is lost."""
    git("checkout", "--", ".", cwd=cwd, check=False)
    git("clean", "-fdq", cwd=cwd, check=False)


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_load(st: State, args) -> dict:
    # Read every source before touching the loaded state, so a failed load
    # leaves the previous one intact.
    sources: dict[str, dict] = {}
    bodies: dict[str, str] = {}

    def take(text: str, src: dict) -> str:
        p = plan.extract(text, src.get("ref") or src.get("path", "input"))
        name = "epic.md" if p.get("kind") == "epic" else f"story-{plan.story_key(p)}.md"
        bodies[name] = text
        sources[name] = src
        return name

    if args.files:
        for f in args.files:
            try:
                text = Path(f).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise DispatchError(f"cannot read {f}: {exc}") from exc
            take(text, {"kind": "file", "path": str(Path(f).resolve())})
    else:
        tracker = _load("tracker")
        forge = tracker.forge()
        refs = list(args.story or [])
        if args.epic:
            name = take(forge.get(tracker.number(args.epic)), {"kind": "tracker", "ref": args.epic})
            epic = plan.extract(bodies[name])
            refs += [str(s.get("issue")) for s in plan.as_list(epic.get("stories"))
                     if plan.issue_number(s.get("issue"))]
        for ref in refs:
            take(forge.get(tracker.number(ref)), {"kind": "tracker", "ref": ref})
    st.work.mkdir(parents=True, exist_ok=True)
    for old in st.work.glob("*.md"):
        old.unlink()
    for name, text in bodies.items():
        (st.work / name).write_text(text, encoding="utf-8")
    st.data = {"sources": sources, "base": args.base or default_base(),
               "trees": str(st.root.parent / f"{st.root.name}-tracks")}
    st.save()
    epic, stories = st.plans()
    errs = plan.validate_set(epic, stories)
    planned = {plan.story_key(s) for s in stories}
    unplanned = [str(s.get("id")) for s in plan.as_list((epic or {}).get("stories")) if str(s.get("id")) not in planned]
    return {"ok": not errs, "loaded": sorted(sources), "unplanned_stories": unplanned,
            "errors": errs, "base": st.base, "trees": str(st.trees)}


def ensure_story_branch(st: State, story: dict, stories: dict[str, dict], dry: list | None) -> Path:
    branch = story_branch(story)
    sid = plan.story_key(story)
    integ = st.trees / f"{sid}-integration"
    if dry is not None:
        exists = ok("show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
        if not exists:
            dry.append(f"git branch {branch} {st.base}")
        if not integ.exists():
            dry.append(f"git worktree add {integ} {branch}")
        for up in map(str, plan.as_list(story.get("depends_on"))):
            upstream = stories.get(up)
            if upstream is None:
                continue
            up_branch = story_branch(upstream)
            if not ok("show-ref", "--verify", "--quiet", f"refs/heads/{up_branch}"):
                continue
            if exists and ok("merge-base", "--is-ancestor", up_branch, branch):
                continue
            dry.append(f"git -C {integ} merge --no-ff {up_branch}")
        return integ
    if not ok("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"):
        git("branch", branch, st.base)
    if not integ.exists():
        git("worktree", "add", str(integ), branch)
    # A story starts from the finished work of the stories it depends on.
    for up in map(str, plan.as_list(story.get("depends_on"))):
        upstream = stories.get(up)
        if upstream is None:
            raise DispatchError(f"story {sid} depends on {up}, which has no plan loaded")
        up_branch = story_branch(upstream)
        if not ok("show-ref", "--verify", "--quiet", f"refs/heads/{up_branch}"):
            continue  # already merged and deleted
        if ok("merge-base", "--is-ancestor", up_branch, "HEAD", cwd=integ):
            continue
        try:
            git("merge", "--no-ff", "--no-edit", "-m", f"merge: {up_branch} into {branch}", up_branch, cwd=integ)
        except DispatchError:
            git("merge", "--abort", cwd=integ, check=False)
            raise DispatchError(f"story {sid}: merging upstream {up_branch} conflicts; fix the plan")
    return integ


def cmd_prepare(st: State, args) -> dict:
    if not args.allow_dirty and clean_tree(st.root):
        raise DispatchError("the main checkout has uncommitted changes (use --allow-dirty to proceed)")
    epic, stories = st.plans()
    errs = plan.validate_set(epic, stories)
    if errs:
        return {"ok": False, "errors": errs}
    by_id = {plan.story_key(s): s for s in stories}
    runnable = plan.next_runnable(epic, stories, args.max)
    briefs = st.work / "briefs"
    briefs.mkdir(parents=True, exist_ok=True)
    out = []
    for u in runnable:
        sid, track = u["story"], str(u["track"])
        story = by_id[sid]
        branch = story_branch(story)
        tbranch = f"{branch}--{track}"
        tree = st.trees / f"{sid}-{track}"
        dry: list | None = [] if args.plan else None
        ensure_story_branch(st, story, by_id, dry)
        unit = f"{sid}/{track}"
        t = track_of(story, track)
        if dry is not None:
            dry.append(f"git worktree add -b {tbranch} {tree} {branch}")
            base_state = "not run"
        else:
            if not tree.exists():
                git("worktree", "add", "-b", tbranch, str(tree), branch)
            if plan.is_command(t.get("verify")):
                passed = baseline(st, unit, str(t.get("verify")), tree, args.baseline_timeout)
                base_state = "pass" if passed else "fail"
            else:  # check reports the missing verify; nothing to baseline
                base_state = "not run"
            st.set_status(sid, track, "running")
        weak = base_state == "pass" and t.get("verify_baseline") != "pass"
        text = plan.brief(story, track) + (
            f"\n\n## Where to work\nWork only in `{tree}` (cd there first). "
            f"Your branch is `{tbranch}`; commit there.\n")
        if weak:
            text += WEAK_BRIEF.format(verify=t.get("verify"))
        bpath = briefs / f"{sid}-{track}.md"
        bpath.write_text(text, encoding="utf-8")
        item = {"unit": unit, "kind": u["kind"], "worktree": str(tree), "branch": tbranch,
                "story_branch": branch, "owns": u["owns"], "verify": u["verify"], "brief": str(bpath),
                "baseline": base_state, "weak_check": weak}
        if dry is not None:
            item["would_run"] = dry
        out.append(item)
    return {"ok": True, "dry_run": bool(args.plan), "units": out,
            "waiting": [] if out else report_waiting(epic, stories)}


def report_waiting(epic, stories) -> list[str]:
    nodes, deps = plan.units(epic, stories)
    status = {u: n["track"].get("status", "todo") for u, n in nodes.items()}
    return [f"{u} waits on {', '.join(d for d in deps[u] if status.get(d) != 'done')}"
            for u in sorted(nodes) if status[u] == "todo"]


def cmd_check(st: State, args) -> dict:
    sid, track = split_unit(args.unit)
    story = st.story(sid)
    t = track_of(story, track)
    branch = story_branch(story)
    tree = st.trees / f"{sid}-{track}"
    if not tree.is_dir():
        raise DispatchError(f"no worktree for {args.unit} at {tree}")
    findings: list[str] = []
    dirty = clean_tree(tree)
    if dirty:
        findings.append(f"uncommitted changes: {', '.join(dirty[:10])}")
    commits = git("log", "--oneline", f"{branch}..HEAD", cwd=tree).splitlines()
    if not commits:
        findings.append("no commits on the track branch")
    changed = [c for c in git("diff", "--name-only", f"{branch}...HEAD", cwd=tree).splitlines() if c]
    outside = [c for c in changed if not plan.covered_by(c, plan.as_list(t.get("owns")))]
    if outside:
        findings.append(f"changed outside owns: {', '.join(outside)}")
    weak = weak_check(st, args.unit, t)
    if weak and changed and not any(TEST_FILE.search(c) for c in changed):
        findings.append(f"verify passed before any work and the diff adds or changes no test, "
                        f"so the check cannot fail: {t.get('verify')}")
    verify_ok, tail = None, ""
    if not plan.is_command(t.get("verify")):
        tail = "not run: no verify command"
        findings.append("the plan has no verify command for this track")
    elif dirty:
        tail = "not run: the worktree has uncommitted changes"
    else:
        verify_ok, tail = run_shell(str(t.get("verify")), tree, args.timeout)
        restore(tree)
        if not verify_ok:
            findings.append(f"verify failed: {t.get('verify')}")
    owns = " ".join(f"'{p}'" for p in plan.as_list(t.get("owns")))
    return {"ok": not findings, "unit": args.unit, "findings": findings, "commits": commits,
            "changed": changed, "outside_owns": outside, "verify": t.get("verify"),
            "verify_passed": verify_ok, "verify_tail": tail, "weak_check": weak,
            "review": f"git -C '{tree}' diff {branch}...HEAD -- {owns}"}


def cmd_block(st: State, args) -> dict:
    sid, track = split_unit(args.unit)
    track_of(st.story(sid), track)
    st.set_status(sid, track, "blocked", args.note)
    return {"ok": True, "unit": args.unit, "status": "blocked", "note": args.note}


def cmd_merge(st: State, args) -> dict:
    sid, track = split_unit(args.unit)
    story = st.story(sid)
    t = track_of(story, track)
    status = {str(x.get("id")): x.get("status", "todo") for x in plan.as_list(story.get("tracks"))}
    if status[track] != "running":
        raise DispatchError(f"{args.unit} is {status[track]}, not running")
    waiting = [d for d in map(str, plan.as_list(t.get("depends_on"))) if status.get(d) != "done"]
    order = [str(x) for x in plan.as_list((story.get("integration") or {}).get("merge_order"))]
    if track in order:
        waiting += [x for x in order[: order.index(track)] if status.get(x) != "done" and x not in waiting]
    if waiting:
        return {"ok": False, "unit": args.unit, "findings": [f"merge {', '.join(waiting)} first"]}
    tree = st.trees / f"{sid}-{track}"
    dirty = clean_tree(tree) if tree.is_dir() else []
    if dirty:  # merging would delete this worktree, and these files with it
        return {"ok": False, "unit": args.unit,
                "findings": [f"uncommitted changes in the worktree: {', '.join(dirty[:10])}; "
                             "commit them and re-run check first"]}
    by_id = {plan.story_key(s): s for s in st.plans()[1]}
    integ = ensure_story_branch(st, story, by_id, None)
    branch = story_branch(story)
    tbranch = f"{branch}--{track}"
    try:
        git("merge", "--no-ff", "--no-edit", "-m", f"merge({sid}): track {track}", tbranch, cwd=integ)
    except DispatchError:
        conflicts = git("diff", "--name-only", "--diff-filter=U", cwd=integ, check=False).splitlines()
        git("merge", "--abort", cwd=integ, check=False)
        if not conflicts:
            raise  # an environment failure (identity, hooks, locks): fix it, don't blame the plan
        note = f"merge conflict in {', '.join(conflicts)}; the plan's ownership is wrong"
        st.set_status(sid, track, "blocked", note)
        return {"ok": False, "unit": args.unit, "findings": [note]}
    sha = git("rev-parse", "--short", "HEAD", cwd=integ)
    st.set_status(sid, track, "done", f"merged {sha}")
    if tree.exists():
        git("worktree", "remove", "--force", str(tree))
    git("branch", "-D", tbranch, check=False)
    return {"ok": True, "unit": args.unit, "merged": sha, "story_branch": branch}


def cmd_integrate(st: State, args) -> dict:
    story = st.story(args.story)
    pending = [str(x.get("id")) for x in plan.as_list(story.get("tracks")) if x.get("status") != "done"]
    if pending:
        return {"ok": False, "story": args.story, "findings": [f"tracks not done: {', '.join(pending)}"]}
    by_id = {plan.story_key(s): s for s in st.plans()[1]}
    integ = ensure_story_branch(st, story, by_id, None)
    dirty = clean_tree(integ)
    if dirty:  # verify on an unknown tree means nothing, and cleanup would erase it
        return {"ok": False, "story": args.story,
                "findings": [f"uncommitted changes in {integ}: {', '.join(dirty[:10])}; "
                             "commit or remove them first"]}
    results, findings = [], []
    commands = [c for c in [(story.get("integration") or {}).get("verify"), story.get("verify")]
                if plan.is_command(c)]
    if not commands:
        findings.append("the plan has no verify command for this story (integration.verify or verify)")
    for command in dict.fromkeys(commands):
        passed, tail = run_shell(str(command), integ, args.timeout)
        restore(integ)
        results.append({"command": command, "passed": passed, "tail": tail})
        if not passed:
            findings.append(f"failed: {command}")
    pushed = False
    if not findings and args.push and git("remote", check=False):
        git("push", "-u", "origin", story_branch(story), cwd=integ)
        pushed = True
    return {"ok": not findings, "story": args.story, "branch": story_branch(story), "checks": results,
            "findings": findings, "pushed": pushed}


def cmd_report(st: State, args) -> dict:  # noqa: ARG001
    epic, stories = st.plans()
    rows, done_stories = [], []
    for s in stories:
        tracks = plan.as_list(s.get("tracks"))
        for t in tracks:
            rows.append({"unit": f"{plan.story_key(s)}/{t.get('id')}", "status": t.get("status", "todo"),
                         "note": t.get("note", "")})
        if tracks and all(t.get("status") == "done" for t in tracks):
            done_stories.append(plan.story_key(s))
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in plan.STATUSES}
    return {"ok": True, "counts": counts, "units": rows, "stories_ready_to_integrate": done_stories,
            "next_runnable": [u["unit"] for u in plan.next_runnable(epic, stories, 99)],
            "waiting": report_waiting(epic, stories)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Mechanical steps of wave-dispatcher (git, plans, status).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("load")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--epic"); g.add_argument("--story", nargs="+"); g.add_argument("--files", nargs="+")
    p.add_argument("--base", help="branch new story branches start from (default: origin/HEAD, main or master)")
    p = sub.add_parser("prepare"); p.add_argument("--max", type=int, default=3)
    p.add_argument("--plan", action="store_true", help="dry run: write briefs, print the git commands, change nothing")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--baseline-timeout", type=int, default=300,
                   help="seconds for the one-time verify run that detects a check that cannot fail")
    p = sub.add_parser("check"); p.add_argument("unit"); p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("merge"); p.add_argument("unit")
    p = sub.add_parser("block"); p.add_argument("unit"); p.add_argument("--note", required=True)
    p = sub.add_parser("integrate"); p.add_argument("story"); p.add_argument("--push", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    sub.add_parser("report")
    args = ap.parse_args()
    try:
        st = State()
        result = globals()[f"cmd_{args.cmd}"](st, args)
    except (DispatchError, plan.PlanError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    except SystemExit as exc:  # tracker.py reports its failures with sys.exit("tracker: ...")
        if exc.code in (None, 0):
            raise
        print(json.dumps({"ok": False, "error": str(exc.code)}, indent=2))
        return 2
    except (OSError, ValueError) as exc:  # includes a corrupt state.json (JSONDecodeError)
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
    raise SystemExit(main())
