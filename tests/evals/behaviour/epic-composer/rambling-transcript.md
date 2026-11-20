# Case: a rambling transcript with two candidate outcomes

## Input

> **Transcript, 34 min.** Priya: support keeps asking for a way to see who
> changed an account. Tom: that's audit, we could also just email a digest.
> Priya: the ask is "who changed it", not a digest. Tom: digest is easier, we
> could ship it Friday. Dee: Friday is tight, we still have the billing bug.
> Priya: also the export thing from last week, is that the same? Dee: no.
> Tom: fine, audit log Friday, digest next quarter. Priya: and it has to be
> searchable, support won't scroll. Dee: by user or by field? Priya: both?
> Tom: let's not decide that here. **End.**

## Expected properties

- Exactly **one** outcome is proposed, in observable terms — not two epics, and
  not "audit and digest".
- The Friday-vs-billing conflict, the digest deferral, and the
  user-vs-field question appear as **open questions / risks / scope exclusions**,
  not as silent assumptions.
- 3–8 acceptance criteria, each checkable without reading the code (e.g. "a
  change to an account appears in the log within N seconds, filterable by
  user"), each with a `when … then …`.
- The unmentioned-but-implied work (retention, permissions on who may read the
  log) is either an explicit exclusion or a stated unknown — it is not invented
  as a story.
- If the input genuinely cannot support one outcome, the skill says so and asks
  one question instead of drafting.
