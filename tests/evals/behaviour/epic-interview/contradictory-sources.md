# Case: two sources that contradict each other

## Input

> **Issue #412:** "Offline mode for the reader. Cached articles must be readable
> with no network. Closes the field-team request."
>
> **Design doc, §2:** "The reader is a browser app; there is no offline support
> and none is planned. Storage is server-side only."

## Expected properties

- The contradiction is **named explicitly** — the skill does not pick a reading
  silently or average them into "mostly works offline".
- It asks the **smallest** set of questions (who decides: product or the design
  doc's owner; what "no network" means for a browser app), not a questionnaire.
- It does **not** draft an Epic, stories, or acceptance criteria.
- Assumptions that would have been needed are listed as such, each tied to the
  question that resolves it.
- The answer is short: no restating the inputs back as prose.
