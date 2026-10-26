---
read_when: "Writing React components, stores, or frontend services"
paths:
  - "{{FRONTEND_PATH}}/**"
---

# Frontend Conventions

## State Management

- {{STATE_MANAGER}} stores only for client state ({{FRONTEND_STORE_EXAMPLES}})
- Store actions are pure wrappers over service calls; side effects isolated
- No global mutable singletons outside {{STATE_MANAGER}}
- No additional state management libraries without explicit justification

## API Integration

- All API calls through typed service modules — no direct fetch in components
- Service calls return either `data` or `error` envelope
- Error boundaries and typed error envelopes at component boundaries

## Security

- Auth tokens stored in memory (never localStorage for sensitive tokens)
- Sanitize all external inputs; never trust client-side data

## Stack

- React {{REACT_VERSION}} + TypeScript + Vite
- {{UI_LIBRARY}} components{{#TAILWIND}} + Tailwind CSS{{/TAILWIND}}
- Vitest + MSW + React Testing Library for tests
- {{E2E_TOOL}} for E2E
{{#ZOD_VALIDATION}}- Zod for schema validation{{/ZOD_VALIDATION}}

## Type Safety

- No `as any` casts — use proper generics, type widening, or `as never` for test mocks
- No `dangerouslySetInnerHTML` or raw `innerHTML` — use DOMPurify or text content

## Code Hygiene

- No `console.log` in production code — remove or gate behind `import.meta.env.DEV`
- {{STATE_MANAGER}} stores ≤ 300 lines; split into sub-stores with `immer` middleware when larger

## Testing

- Security-critical components (auth, session management): 90%+ coverage
- {{STATE_MANAGER}} stores: 70%+ coverage
- Test stack: Vitest + MSW + React Testing Library; {{E2E_TOOL}} for E2E

### Suite Health (BLOCKING — no exceptions)

The Vitest suite is a binary signal. Either it is green and trusted, or it is a liar.

- **Zero failing tests may be checked in.** `{{TEST_FRONTEND_CMD}}` on a clean checkout MUST exit zero.
- **Zero unconditional skips may be checked in.** Forbidden: `it.skip(...)`, `test.skip(...)`, `describe.skip(...)`, `.todo`, `xit`, `xdescribe`.
- **{{E2E_TOOL}} runtime skips are permitted** only inside a conditional (`if (!isMobile) { test.skip(...) }`).
- **Test drift is a bug, not a placeholder.** When you change a component prop, aria-label, store field, service signature, or API response shape, update the co-owning tests in the same commit.
- **Wall-clock-sensitive assertions MUST use relative dates** or `vi.useFakeTimers()`. Hardcoded ISO strings that imply "recent" will rot.
- **Deterministic test infrastructure.** Any randomness must be seedable or faked.

### Test Runner Discipline

- **Vitest and {{E2E_TOOL}} have disjoint test files.** `vite.config.ts` MUST set `test.exclude` to include `tests/e2e/**`.
- **MSW handler paths are relative.** The shared handlers register `/api/...` paths.
- **Module-mock shapes must match real exports.** For icon libraries, enumerate the subset the component uses — Vitest rejects `Proxy`-backed factories.

### Mocking Anti-Patterns

- Tests that assert on component text, `aria-label`, store fields, or service method signatures that don't exist in the current codebase
- Wall-clock-dependent assertions without fake timers
- Proxy-backed module mocks
- Hardcoding `XMLHttpRequest` globals when the component now delegates to a service wrapper
