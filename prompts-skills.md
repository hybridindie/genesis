# Epic Scoping Skills

Usage guide for the epic-scoping skills: how to invoke them in each harness and
worked examples. `AGENTS.md` is the concise entrypoint; the genesis harness is
documented in `README.md` and [`docs/agents-sections/`](docs/agents-sections/).

- Architecture, golden rule and file tree:
  [`architecture.md`](docs/agents-sections/architecture.md)
- Skills, templates, doctrine and harness layout:
  [`skills-and-references.md`](docs/agents-sections/skills-and-references.md)
- The epic → story → task pipeline and its outputs:
  [`workflow.md`](docs/agents-sections/workflow.md)
- Editing hooks and versioning: [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md)

## Harness setup

Every skill can be invoked **two ways**:

- **Directly** — type its slash command (the same name in every harness; see
  the [command table](#example-workflows)).
- **Automatically** — the harness loads the matching skill when your request
  fits its `description` (and `when_to_use`, where supported), so you can just
  describe your goal without naming a command.

### OpenCode

- **Directly:** each skill has a `commands` entry in `.opencode/opencode.json`
  (OpenCode skills are model-invoked only, so the commands are the slash path).
- **Automatically:** OpenCode discovers `.agents/skills/<name>/SKILL.md` on its
  own (no config) and picks a skill by its `description`.
- Config: `.opencode/opencode.json` sets `instructions` → `AGENTS.md` and the
  `commands`. Restart OpenCode after changing config.
- Docs: [OpenCode Skills](https://opencode.ai/docs/skills)

### Claude Code

- **Directly:** skills double as slash commands and accept `$ARGUMENTS`.
- **Automatically:** Claude loads a skill when your request matches its
  `description`/`when_to_use` — no command needed.
- Config: `.claude/CLAUDE.md` imports `AGENTS.md` (everything else loads on
  demand). Claude Code reads `.claude/skills/`, where each skill is a generated
  pointer to its `.agents/skills/` file.
- Docs: [Claude Code Skills](https://code.claude.com/docs/en/skills)

## Example workflows

Each task uses the **same slash command in every harness** — the skill's name:

| Task | Command |
|------|---------|
| Compose an Epic | `/epic-composer` |
| Close gaps (interview) | `/epic-interview` |
| Lint acceptance criteria | `/epic-acceptance-linter` |
| Decompose Epic → stories | `/story-decomposer` |
| Story → tasks | `/task-decomposer` |
| Review a plan with a second model | `/plan-reviewer` |
| Run the planned work | `/wave-dispatcher` |
| Ship approved Epics unattended | `/factory` |
| Ship a PR | `/ship-pr` |

Type the command from the `/` menu, then paste your content after it — or just
describe your goal and let the matching skill auto-load from its `description`.
(In OpenCode these names are `commands` entries in `.opencode/opencode.json`; in
Claude Code they are the skills themselves.)

To adapt any example, replace the **[bracketed placeholder]** with your own
material and keep the rest.

---

### 1. Compose an Epic from source material

**Use when** you have raw transcripts, docs, or notes and want a structured,
traceable Epic.

Run the **Compose an Epic** command and paste your source material:

```
[Paste everything you have: meeting transcripts, product docs, business
goals, constraints, rough notes. More context = fewer follow-up questions.]

--- example ---
Planning meeting, 2024-01-15
PM:  Users can only export reports as CSV and keep asking for PDF.
Eng: The export pipeline is synchronous — large PDFs will time out.
PM:  Scope it to reports under 500 rows for the first release.
Product doc v2, §3.1: "Users can export reports in PDF and CSV. PDF export
applies to standard report templates."
```

**You get** a drafted Epic — current/future state, MVP vs. Phase-2 scope, NFRs,
outcome-focused acceptance criteria, a story map with parallel waves, and a short risk list
— after the skill asks the 2–3 critical questions it couldn't answer from your
material.

> **Brownfield?** Run this inside an existing codebase and Phase 0 also reads
> your `AGENTS.md`/`README`, package manifest, and test conventions, recording
> them as Project Constraints — no extra input needed.

---

### 2. Close gaps on a rough Epic draft (interview)

**Use when** you have a partial Epic and want to know what's missing before
finalizing.

Run the **Close gaps** command and paste your draft:

```
Epic: [one-line title]
Problem: [what's broken today]
Scope: [what's in / out]
Acceptance: [any criteria you have so far]

--- example ---
Epic: PDF Export for Reports
Problem: Users can only export CSV today.
Scope: PDF export for reports under 500 rows.
Acceptance: Users can export a report as PDF.
```

**You get** targeted questions in waves — critical blockers first (auth,
success metrics, edge cases), then clarifiers — with anything you can't answer
marked `[BLOCKED]`. The skill closes gaps; it does not rewrite the Epic.

---

### 3. Lint acceptance criteria

**Use when** you have acceptance criteria and want a quality pass.

Run the **Lint acceptance criteria** command and paste your criteria:

```
[Paste your acceptance criteria, one per line.]

--- example ---
AC1: Users can export reports as PDF.
AC2: The export is fast.
AC3: PDF export works for all report types.
AC4: The system handles errors gracefully.
```

**You get** a per-criterion review flagging vague terms ("fast" — no
threshold), unobservable outcomes ("gracefully"), and scope conflicts (AC3 vs.
a 500-row limit), plus strengthened rewrites and an optional
`Ready` / `Needs work` / `Blocked` verdict.

---

### 4. Decompose a ready Epic into stories

**Use when** your Epic has an outcome and acceptance criteria and you want
shippable stories plus a parallel execution map. The Epic's acceptance criteria are what get decomposed.

Run the **Decompose Epic** command and paste the Epic:

```
Epic: [title]
AC1: When [trigger], then [observable outcome], so that [value].
AC2: ...
NFR: [any performance / security / etc. constraints]

--- example ---
Epic: PDF Export for Reports
AC1: When a user exports a report under 500 rows, then the system produces a
PDF within 10 seconds, so that the user does not wait or retry.
AC2: When a user selects PDF format, then the export uses the standard report
template, so that output is consistent across reports.
AC3: When a PDF export fails, then the user sees an error with a retry option,
so that they can recover without losing context.
NFR: PDF generation < 10s p95 for reports under 500 rows.
```

**You get** one story issue body per story with acceptance criteria, an
estimate, the files it owns, its wave, and a shared contract where needed; plus
an execution map (Wave · Story · Owns · Depends on · Parallel with · Verify) and
a coverage note mapping every AC to a story.

---

### 5. Break a story into AI-executable tasks

**Use when** you have a drafted story and want concrete engineering tasks an AI
agent can implement. The story must include acceptance criteria.

Run the **Story → tasks** command and paste the story:

```
Story: [title]
As a [user], I want [action], so that [value].
AC1: Given [context], when [action], then [outcome].
AC2: ...
Estimate: [S / M / L]
Feature flag: [name, if any]

--- example ---
Story: Export small report as PDF
As a report viewer, I want to export a report as PDF, so that I can share it
with stakeholders.
AC1: Given a report under 500 rows, when the user clicks "Export as PDF", then
the system generates and downloads a PDF within 10 seconds.
AC2: Given the PDF service is unavailable, when the user clicks "Export as
PDF", then the system shows an error with a retry button.
Estimate: S
Feature flag: pdf_export_enabled
```

**You get** a task checklist structured for delegation: a shared contract
first (e.g. the `POST /api/reports/{id}/export` response shape), independent
tracks with disjoint file ownership and a verify command each, and an
integration task last — every task naming `owns`, `depends`, `verify`, and the
AC it serves.

---

### Chaining the skills end-to-end

The skills hand off in sequence; run them in order and review at each
checkpoint:

1. **Compose** → an Epic issue with a parallel story map; review it and close
   blockers with the interview if needed.
2. **Decompose** → story issues, each with `owns`, waves, and a shared contract.
3. **Tasks** → run task-decomposer on the stories you are about to dispatch;
   it appends the checklist to each story.
4. **Dispatch** with `/wave-dispatcher`: it starts every runnable track in its
   own worktree, checks and merges each one, and integrates finished stories.
   `/wave-dispatcher --plan` shows what would start without touching git.
5. **Ship** each story branch with `/ship-pr`.

Between steps 2 and 3, `/plan-reviewer` gets a second model's verdict on the
stories before anything is dispatched. Choose that model with
`PLAN_REVIEW_MODEL` (for example `export PLAN_REVIEW_MODEL=provider/model`): a
cheap model that is **not** the one writing the code. Unset, it falls back to
`opencode/big-pickle`, a free OpenCode Zen model that may be retired. Only
blocking findings (contradictions, unverifiable criteria, ownership gaps,
scope conflicts, an impossible dependency order) send the plan back; deferred,
task-level ones go to task-decomposer in step 3.

### Run the factory

To have approved Epics picked up and shipped without prompting each step, start
the factory in a session and leave it open:

```
/factory
```

```
/factory --epic #42 --limit 2000000
```

The first form works every approved open Epic, oldest first, then exits; the
second runs one named Epic with a 2,000,000-token budget and stops. Approve an
agent-drafted Epic by adding `factory:approved` to it. Each round prints a
status line such as:

```
factory #42 round 3: done 4/7 · running 2 · blocked 0 · escalated 1 · budget 1200000/2000000 (60%, ok)
```

Answer any question it posts on a story labelled `factory:needs-input`; labels,
escalation and budget are described in the README's "The factory" section.

You rarely run every command by hand: epic-composer can hand off to
story-decomposer, and story-decomposer can invoke task-decomposer per story.
Optional quality passes (linter, rubrics) are there when you want a stricter
review.

### Refining a backlog later

Return to the **Decompose Epic** command any time to groom the backlog, split
an in-progress story, or add one. For a mid-sprint split, describe what's done
and what's left:

```
Story 2 (Handle large report boundary) is in progress. PDF generation for
reports over 500 rows is timing out. Story 1 (basic export for small reports)
is complete. Split the remaining work.
```

The decomposer preserves completed work, creates new stories for the
remainder, re-runs task breakdown on them, and re-maps dependencies and sprints.
