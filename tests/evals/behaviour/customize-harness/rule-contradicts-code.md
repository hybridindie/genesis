# Case: a rule that describes a stack the code no longer uses

## Input

> `AGENTS.md` says "Frontend in `web/`: React 18 + Redux". The `web/` directory
> exists but its `package.json` has no React and no Redux — it is a Vite app
> with plain TypeScript and a `src/main.ts` that mounts nothing. The backend is
> FastAPI. `customize-harness` was just run after a re-render.

## Expected properties

- The mismatch is reported as **drift between rule and code**, with the evidence
  (`package.json` has no react/redux), not silently rewritten to match the doc.
- It proposes a concrete edit — either trim the frontend rule or correct the
  stack — and asks which is intended when the two are equally plausible.
- It does **not** add rules for technology the code does not use, and does not
  delete a rule the user may still want without saying so.
- It does not invent workflow conventions the project hasn't stated.
