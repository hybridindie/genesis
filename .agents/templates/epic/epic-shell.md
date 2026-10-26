<!--
  epic-shell.md — Epic issue body (paste under the issue title `Epic: <outcome>`)
  Referenced by: .agents/skills/epic-composer.md
  version: 4.0.0, owner: John D
-->

**Why**

[The problem, who feels it, and the evidence. Keep it concrete: a user pain, a
measured gap, an incident, a constraint. No solutioning here.]

**Outcome**

[What is observably different when this epic is done. One coherent outcome; if
there are two unrelated outcomes, split the epic.]

**Scope**

- **In:** [the minimum that delivers the outcome]
- **Out:** [explicit exclusions and why]

**Acceptance criteria**

- **AC1:** When [trigger], then [observable behaviour], so that [value].
- **AC2:** …
- **AC3:** …

[3–8 outcomes. If you need more, the epic is too large — split it. Write what a
user or operator observes, not how it is built.]

**Stories (dependency order)**

| # | Story | Size | Priority | Wave | Depends on |
|---|-------|------|----------|------|------------|
| #TBD | Story 1: … | S | P1 | 1 | — |
| #TBD | Story 2: … | M | P1 | 2 | Story 1 |

[Fill `#` once the story issues exist. Size S/M/L; priority P0–P2; wave numbers
match the parallel map below.]

**Parallelization map**

- **Shared contract:** [interface / type / schema / file format / API both
  sides need — or "none"]
- **Wave 1 (parallel):** Story …
- **Wave 2 (parallel, after Wave 1):** Story …, Story …
- **Integration:** Story … [merge, end-to-end verification]

[Default to parallel. Put a story in a later wave only for a real dependency,
and say what the dependency is.]

**Constraints and non-functional requirements**

- [technical, security, performance, compliance, or "none known"]

**Risks and open questions**

- [risk → mitigation / owner, or a question that blocks a story]

**Success measures**

- [outcome metric, leading indicator, and whether the baseline exists]

**Definition of done**

- [ ] All acceptance criteria met or explicitly descoped with a reason
- [ ] Every story traced to an AC or an explicit constraint
- [ ] Parallel waves and shared contracts are accurate
- [ ] Open questions resolved or assigned
