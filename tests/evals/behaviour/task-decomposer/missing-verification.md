# Case: tasks with no verification and overlapping ownership

## Input

> **Story #13 — Export endpoint and button.** Part of #11.
> AC1: the reader downloads a PDF. AC2: an empty report still downloads.
>
> Tasks:
> - Add the endpoint.
> - Add the button.
> - Make sure `src/report/pdf.py` is covered.
>
> Files: `src/report/routes.py`, `src/report/pdf.py`, `web/src/report/Export.tsx`.

## Expected properties

- Every task gets an **exact verify command** (or is marked as needing one),
  not "make sure it works".
- The ownership conflict is surfaced: `src/report/pdf.py` is claimed by this
  story's files while the task says "make sure it's covered" — it belongs to the
  renderer story, so either the file is removed here or the task becomes a
  read-only check.
- Tasks are ordered so each ends in a green state, and each names the AC it
  serves.
- Nothing outside the stated scope is invented (no analytics, no auth, no new
  export formats).
- If the story cannot be made executable as written, the skill says what is
  missing instead of guessing.
- Any plan it writes passes `plan.py check`; it reports the check's output
  rather than asserting the plan is valid.
