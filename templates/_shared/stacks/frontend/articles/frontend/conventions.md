---
read_when: "Writing frontend components, pages, state, or API service modules"
paths:
  - "{{FRONTEND_PATH}}/**"
---

# Frontend Conventions

Test discipline (red first, no committed skips, determinism) is in
`testing.md`; this file adds only frontend specifics.

## MUST

- API calls go through typed service modules, never `fetch` in a component.
  Services return data or a typed error the UI can render.
- Validate external data at the edge (schema validation such as zod) before
  it reaches components or state.
- The frontend never talks to the database directly; it goes through the API.
- No `as any`. Use generics or narrowing; `as never` is acceptable in test
  mocks only.
- No `dangerouslySetInnerHTML` or raw `innerHTML` with untrusted content.
- Sensitive tokens are not stored in `localStorage`.
- No `console.log` in shipped code; gate debug output behind a dev flag.

## SHOULD

- Server state through the project's data layer; client state in the
  project's store library. Don't add a second state library without a reason
  in the PR.
- Split a store or component when it grows past ~300 lines.
- Keep unit/component tests and E2E tests in separate files and runners
  (exclude the E2E directory from the unit runner).
- When a prop, label, store field, or API shape changes, update the tests
  that depend on it in the same commit.
- Use fake timers or relative dates for time-dependent assertions.

## Stack

{{FRONTEND_STACK}}
