<!--
  task-breakdown-shell.md — parallel task block appended under `**Tasks**` in a story issue
  Referenced by: .agents/skills/task-decomposer.md
  version: 1.0.0, owner: John D
-->

### Parallelization

- **Shared contract:** [interface / type / schema / file format both tracks need]
  — owner: [task or track] — verify: `<command>`
- **Integration:** [merge order + end-to-end check] — after all tracks.

| Track | Owns | Depends on | Parallel with | Verify |
|-------|------|------------|---------------|--------|
| Contract | `<path/>` | — | — | `<command>` |
| A — [name] | `<path/>` | Contract | B | `<command>` |
| B — [name] | `<path/>` | Contract | A | `<command>` |
| Integration | `<path/>` | A, B | — | `<command>` |

### Tasks

**Contract (sequential — unblocks the tracks)**
- [ ] **T1** — [define the interface/type/schema/file format] in `<path/>` — owns `<path/>` — verify `<command>`

**Track A — [name] (parallel after T1)**
- [ ] **T2** — [verb + specific change] in `<path/>` — owns `<path/>` — depends T1 — verify `<command>`
- [ ] **T3** — [test for T2] in `<test path/>` — owns `<test path/>` — depends T2 — verify `<command>`

**Track B — [name] (parallel after T1)**
- [ ] **T4** — [verb + specific change] in `<path/>` — owns `<path/>` — depends T1 — verify `<command>`

**Integration (sequential — after all tracks)**
- [ ] **T5** — [merge tracks / run the end-to-end check] — verify `<command>`

### Dispatch notes

- One track per subagent or team; each brief includes the contract, the owned
  paths, and the verify command.
- Do not edit a path owned by another track; raise it as a follow-up instead.
- Merge in the order above; the integration task owns the final verification.
