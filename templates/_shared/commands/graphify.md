---
description: Build or update the graphify knowledge graph for a path
---

Run the `graphify` CLI for `$ARGUMENTS` (a source directory; default: the
project's source root — `src/`, `backend/src/`, or `.` depending on layout).

1. `command -v graphify` — if it is missing, say so and stop. Do not install it.
2. If the path contains GDScript (`*.gd`): `graphify-gdscript --check`. graphify
   has no GDScript extractor of its own; this machine-level patch (genesis
   `system/bin`, run once per graphify install or upgrade) adds it. If the check
   fails, tell the user to run `graphify-gdscript` (it installs
   `tree-sitter-language-pack` into graphify's environment) and stop: a graph
   built without it silently has no `.gd` nodes.
3. `graphify --help` once to confirm the current build/update and labeling subcommands.
4. Build or update the graph for the path, then label its communities.
5. Report the graph output directory and a two-line summary. Do not dump the graph.
