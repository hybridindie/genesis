---
description: Build or update the graphify knowledge graph for a path
---

Run the `graphify` CLI for `$ARGUMENTS` (a source directory; default: the
project's source root — `src/`, `backend/src/`, or `.` depending on layout).

1. `command -v graphify` — if it is missing, say so and stop. Do not install it.
2. `graphify --help` once to confirm the current build/update and labeling subcommands.
3. Build or update the graph for the path, then label its communities.
4. Report the graph output directory and a two-line summary. Do not dump the graph.
