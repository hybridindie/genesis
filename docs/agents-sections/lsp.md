# LSP and Language Servers

On-demand section — read when enabling LSP, debugging missing diagnostics, or
asking why a harness cannot see go-to-definition.

## OpenCode v2: config kept, servers not run

OpenCode v2 **accepts and preserves** the `lsp` key but does not run language
servers, expose LSP tools, or produce LSP diagnostics
([migration notes](https://opencode.ai/docs/migrate-v1)). Use the project's
lint, type-check and compiler commands instead — `/preflight` already runs
them.

The only custom entry lives at the machine layer, the Godot bridge below:

| Surface | File |
|---|---|
| Machine layer | `system/agents/opencode.jsonc` → `~/.config/opencode/opencode.jsonc` |

```jsonc
"lsp": {
  "godot": { "command": ["godot-lsp"], "extensions": [".gd"] }
}
```

It is inert under v2 and kept so the setting is ready if OpenCode runs servers
again. Project templates ship no `lsp` block: a `.gd` server in a Python-only
project describes a language it does not use. A Godot project that wants the
bridge adds the entry to its own `.opencode/opencode.json`. Don't add more
entries expecting diagnostics.

## Claude Code: plugins

Claude Code has no `lsp` key in `settings.json`; language servers come from
plugins. Install an official code-intelligence plugin for the language, or write
a plugin with an `.lsp.json` (or an `lspServers` manifest key) naming the server
command and the file extensions it handles
([code intelligence](https://code.claude.com/docs/en/plugins/code-intelligence)).
The harness does not ship one: it is a per-machine choice, not project config.

An IDE connection (`/ide`) also feeds the editor's diagnostics to Claude.

## Godot bridge (`godot-lsp`)

Godot 4's **editor listens** on TCP `127.0.0.1:6005` while a project is open,
instead of exposing a stdio process. `system/bin/godot-lsp` connects to that
port and pipes the socket to stdin/stdout, so any stdio LSP client (a Claude
Code `.lsp.json`, Zed, or a future OpenCode) can use it. `system/install.sh`
installs it to `~/.local/bin/godot-lsp`.

- **The editor must already be running** with the project open. With no
  listener the bridge prints one line to stderr and exits without writing to
  stdout, so the client gets no server rather than a corrupt stream.
- **The port is per-editor.** If Editor Settings → Network → Language Server →
  Remote Port changed, set `GODOT_LSP_PORT` (and `GODOT_LSP_HOST`) in the
  client's environment. Two open Godot projects share port 6005; the bridge
  attaches to whichever editor owns it.
