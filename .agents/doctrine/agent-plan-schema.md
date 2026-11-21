<!--
  agent-plan-schema.md — the machine-readable plan carried by Epic and story issues
  Referenced by: epic-composer, story-decomposer, task-decomposer, wave-dispatcher
  version: 1.3.0, owner: John D
  Single source of truth for the `agent-plan` block. `.agents/scripts/plan.py`
  enforces it; skills write it; the dispatcher schedules from it.
-->

# The `agent-plan` block

Every Epic and story issue ends with **one** fenced block that agents read
instead of the prose:

````markdown
```yaml agent-plan
version: 1
kind: story
...
```
````

People read the issue; agents read the block. The tables people see (story map,
parallelization, task checklist) are **generated** from the block by
`plan.py sync` and sit between `<!-- agent-plan:generated -->` markers — never
hand-edit them, edit the block and re-sync. Waves are **computed** from
`depends_on`, never written down, so they cannot drift.

## Why it looks like this

- **One owner per path at a time.** Two units that can run at the same time
  (no `depends_on` path between them) must own disjoint paths. This is what lets
  a lead hand units to parallel subagents without merge conflicts, and
  `plan.py validate` rejects plans that break it.
- **Every unit proves itself.** `verify` is an exact command a subagent runs
  before reporting done. "Tests pass" is not a command.
- **Everything traces.** Stories trace to Epic ACs, tasks to story ACs, so
  coverage gaps show up as validation errors instead of surprises.

## Epic block

```yaml agent-plan
version: 1
kind: epic
epic: "#12"                 # this issue, once created ("#TBD" before)
acs: [AC1, AC2, AC3]        # labels of the 3–8 ACs in the prose above
contracts:                  # shared interfaces between stories; [] if none
  - id: C1
    what: ExportJob response schema
    owner: S1               # the story that lands it
    paths: [backend/export/schema.py]
stories:
  - id: S1                  # stable id; issue numbers come later
    title: Export API returns a PDF job
    issue: "#TBD"
    type: user              # user | spike | technical | bug
    size: M                 # S | M | L (≤ ~3 days); split anything larger
    priority: P0            # P0 | P1 | P2
    acs: [AC1]              # or `constraint: <reason>` for enabling work
    depends_on: []          # story ids whose output this story needs
    owns: [backend/export/**]
    verify: uv run pytest tests/export -q
    status: todo            # todo | running | done | blocked
```

## Story block

```yaml agent-plan
version: 1
kind: story
story: S1                   # the id from the Epic block
epic: "#12"
issue: "#13"
branch: feat/13-export-api  # integration branch the tracks merge into
acs: [AC1]
ac_text:                    # copied into subagent briefs
  AC1: Given a report under 500 rows, when export is requested, then …
depends_on: []              # story ids (same as the Epic's)
owns: [backend/export/**, tests/export/**]
must_not_touch: [frontend/**]
verify: uv run pytest tests/export -q        # story-level end-to-end check
context: >-                 # what a subagent with no other context must know
  The export pipeline is synchronous today; this adds a job API.
tracks:                     # one track = one subagent in one worktree
  - id: contract
    kind: contract          # lands first; every other track depends on it
    owns: [backend/export/schema.py]
    verify: uv run python -c "import backend.export.schema"
    status: todo
  - id: A
    name: API route
    kind: track
    owns: [backend/export/routes.py, tests/export/test_routes.py]
    depends_on: [contract]
    verify: uv run pytest tests/export/test_routes.py -q
    # optional: replaces the story context in this track's brief, for when
    # the story context mentions work this track must not do
    context: Add the route only; the PDF worker is track B.
    # optional, refactors only: verify already passes and must stay green
    # verify_baseline: pass
    # optional: contained | wide | irreversible (see "Merge lanes")
    # lane: irreversible
    status: todo
tasks:                      # written by task-decomposer; PR-sized steps
  - id: T1
    track: contract
    do: Define ExportJob in backend/export/schema.py (new)
    files: [backend/export/schema.py]
    verify: uv run python -c "import backend.export.schema"
    acs: [AC1]
integration:
  merge_order: [contract, A]
  verify: uv run pytest tests/export -q
```

A story without `tasks` is still dispatchable: the subagent works from the
track and the story's context. Add tasks when a track is more than one obvious
change.

## Writing rules

- **Block style for anything with punctuation.** Use one key per line for
  tasks. Inline `{…}` mappings break on `{id}`, `:` or `#` inside values; quote
  a value that contains `: `, ` #`, `{` or starts with `*`, `&`, `!` or `@`.
- **Paths are repo-relative globs.** `src/api/**` (or just `src/api`) for a
  tree, an exact path for a file, `src/*.py` for files directly in `src/`.
  `**` spans directories; `*` stays within one. A track's `owns` must sit inside
  its story's `owns`.
- **Shared generated files need one owner.** Lockfiles (`uv.lock`,
  `package-lock.json`), a new package's `__init__.py`, and registries such as an
  app's router list change whenever a dependency or module is added. Give each
  to exactly one unit per wave, or sequence the units that need it; dispatch
  rejects a diff that touches a path its track does not own.
- **Verify is a command.** `<command>`, `TBD`, `N/A` and blanks are rejected.
- **Verify must be able to fail.** `dispatch.py prepare` runs each track's
  verify once before work starts. If it already passes, the track is flagged
  as a weak check: its brief asks for a failing test first, and `check`
  rejects a diff that adds or changes no test. A refactor that should stay
  green before and after declares `verify_baseline: pass`.
- **Merge lanes follow blast radius, not confidence.** Each track gets a lane
  from what it owns, and the lane decides how its merge is gated:

  | Lane | What it owns | Gate |
  |---|---|---|
  | `irreversible` | anything inside `**/migrations/**`, `**/alembic/**`, `**/*.sql`, `supabase/**`, `deploy/**`, `deployments/**`, `infra/**`, `k8s/**`, `helm/**`, `terraform/**`, `**/*.tf`, or a plan's own `lanes: {irreversible: [...]}` | never auto-merged: `merge` refuses without `--human` |
  | `wide` | a contract track, or a path an Epic contract names | checks plus a diff review |
  | `contained` | everything else | checks |

  `check` also escalates a unit to `irreversible` when its diff touches one of
  those paths, whatever the plan predicted. `lane:` on a track sets it
  explicitly. Irreversible is a closed lane, not a high threshold.
- **Contracts are tracks.** Inside a story, a shared interface is a track with
  `kind: contract`; across stories it is an Epic `contracts` entry owned by one
  story, and dependants list that story in `depends_on`.
- **Status is written by the dispatcher**, not by planners. New plans use
  `todo` or leave it out.
- **Ids are stable.** Never renumber stories, tracks or tasks after dispatch
  starts; add new ones instead.

## Commands

```bash
plan=.agents/scripts/plan.py
python3 $plan check    epic.md story-*.md   # validate + regenerate tables + prose shape + waves
python3 $plan scaffold epic.md --out .      # story-<id>.md skeletons with the plan prefilled
python3 $plan next     epic.md story-*.md   # tracks that can start now (JSON)
python3 $plan brief    story.md --track A   # the subagent brief
```

`.agents/scripts/dispatch.py` runs a plan (load, prepare, check, merge, block,
integrate, report); `wave-dispatcher` is the skill that drives it. Both scripts
need PyYAML; without it they re-run themselves under `uv` to fetch it.
