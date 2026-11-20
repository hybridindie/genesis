# Task list — story #13: Export endpoint and button

Part of #11

### Parallelization

Tasks run in order: T1 creates the endpoint T2 calls, T3 covers the empty case
both paths need. Owns `src/report/routes.py` and `web/src/report/Export.tsx`;
does not touch `src/report/pdf.py`.

### Tasks

- [ ] **T1** Add `POST /reports/{id}/export` returning a job id — verify:
  `pytest tests/report/test_export.py -k endpoint`
- [ ] **T2** Add the Export button that calls it and shows the job id — verify:
  `cd web && npm test -- Export`
- [ ] **T3** Cover the empty report case end to end — verify:
  `pytest tests/report/test_export.py -k empty`

### Dispatch notes

- T1 is the shared contract: T2 cannot pass until it exists.
- Stop after each task in a green state; do not batch T1 and T2 into one commit.
