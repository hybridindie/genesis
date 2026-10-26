<!--
  story-shell.md — Story issue body (title `Story N: <outcome>` or `story(scope): <outcome>`)
  Referenced by: .agents/skills/story-decomposer.md
  version: 3.0.0, owner: John D
-->

Part of #<epic> · Estimate: S/M/L · Wave: N · Depends on: #… · Parallel with: #…

**As a** [actor], **I want** [capability], **so that** [value].

[For a spike or technical story use: **What** … **Why** … instead of the
user-story frame. A story is one vertical slice that can ship on its own.]

**Context**

[The current behaviour, what is missing, and anything the implementer must
know. Link the relevant files, docs, or issues. Mark inferred facts as
inferred.]

**Acceptance criteria**

- [ ] **Given** [state], **when** [action], **then** [observable result].
- [ ] **Given** [edge/empty/failure state], **when** [action], **then**
      [observable result].

[Each criterion must be checkable. One criterion may have several scenarios.]

**Parallelization**

- **Shared contract:** [the interface/type/schema/file format this story and
  other tracks need; name the owner — this story or another]
- **Track A — [name]:** owns `<path/>`, depends on [contract], verifies with
  `<command>`; parallel with Track B.
- **Track B — [name]:** owns `<path/>`, …; parallel with Track A.
- **Integration:** [merge order and end-to-end verification] — after A and B.

[Default to parallel tracks with disjoint file ownership. If the work is truly
sequential, say why. One track should be dispatchable to one subagent or team
without touching another track's files.]

**Files**

- `<path>` (new / modified) — [what changes]

**Tasks**

[Paste the task breakdown from the task-decomposer here — shared contract,
parallel tracks, integration. Each task names what it owns and how to verify.]

**Notes and risks**

- [assumption, risk, rollback, feature flag, or follow-up]

**Done when**

- [ ] Acceptance criteria pass
- [ ] Track verifications pass and the integration check is green
- [ ] No files outside the declared ownership scopes changed
