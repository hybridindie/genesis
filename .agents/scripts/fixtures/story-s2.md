```yaml agent-plan
version: 1
kind: story
story: S2
issue: "#14"
branch: feat/14-export-button
acs: [AC2]
owns: [frontend/src/reports/**]
verify: npm test -- reports
tracks:
  - id: ui
    owns: [frontend/src/reports/ExportButton.tsx, frontend/src/reports/ExportButton.test.tsx]
    verify: npm test -- ExportButton
tasks:
  - id: T1
    track: ui
    do: Add the export button
    files: [frontend/src/reports/ExportButton.tsx]
    verify: npm test -- ExportButton
    acs: [AC2]
```
