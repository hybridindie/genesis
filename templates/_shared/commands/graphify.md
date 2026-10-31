---
description: Build or update the graphify knowledge graph for a path
---

Run the `graphify` CLI for `$ARGUMENTS` (a source directory; default: the
project's source root — `src/`, `backend/src/`, or `.` depending on layout).

1. `command -v graphify` — if it is missing, say so and stop. Do not install it.
{{#STACK_GODOT}}
   Then `graphify-gdscript --check`: graphify has no GDScript extractor of its
   own, and this machine-level patch (genesis `system/bin`) adds it. If the
   command is missing, tell the user to re-run genesis `system/install.sh` (it
   installs it where graphify and a Godot project are present) and stop. If the
   check fails, tell the user to run `graphify-gdscript` (it installs
   `tree-sitter-language-pack` into graphify's environment; re-run after every
   graphify upgrade) and stop: a graph built without it has no `.gd` nodes.
{{/STACK_GODOT}}
2. `graphify --help` once to confirm the current build/update and labeling subcommands.
3. Build or update the graph for the path, then label its communities.
4. Report the graph output directory and a two-line summary. Do not dump the graph.
