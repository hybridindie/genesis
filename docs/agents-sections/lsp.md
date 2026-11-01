# LSP and Language Servers

On-demand section — read when enabling LSP, debugging missing diagnostics, or
asking why a harness cannot see go-to-definition.

The two harnesses are **not** equivalent here. OpenCode has native LSP support
driven by a config key. Claude Code does not.

## OpenCode: native, opt-in

LSP is **off by default**. Omitting the `lsp` key leaves every language server
disabled. Enable it per config surface:

| Surface | File | Reaches |
|---|---|---|
| Machine layer | `system/agents/opencode.jsonc` → `~/.config/opencode/opencode.jsonc` | every project on the machine |
| Project template | `templates/opencode/.opencode/opencode.json` | newly bootstrapped projects |

Both set `"lsp": true`, which seeds every built-in server. Servers start lazily:
one only activates when a file with a matching extension appears **and** its
requirement is satisfiable. A Go file in a repo with no `go.mod` does not start
`gopls`, and a `.dart` file in a repo without the Dart SDK starts nothing.

### Which built-ins will actually run

Detected by extension present in the tree, plus a binary on `PATH`:

| Server | Extensions | Requirement |
|---|---|---|
| `pyright` | `.py`, `.pyi` | `pyright-langserver` (Homebrew `pyright` provides it) |
| `bash` | `.sh`, `.bash`, `.zsh`, `.ksh` | Auto-installs `bash-language-server` via npm |
| `yaml-ls` | `.yaml`, `.yml` | Auto-installs Red Hat `yaml-language-server` via npm |
| `typescript` | `.ts`, `.tsx`, `.js`, ... | `typescript-language-server` |
| `rust` | `.rs` | `rust-analyzer` |
| `gopls` | `.go` | `go` command (`brew install gopls`) |

`gopls` is **not** auto-installed — install it explicitly. The npm-backed
servers download on first use, so a fresh machine needs network access the first
time a `.sh` or `.yml` file is opened.

### Godot (custom server)

OpenCode has no built-in GDScript server, and Godot inverts the usual model: in
Godot 4 the **editor listens** on TCP `127.0.0.1:6005` while a project is open,
instead of exposing a stdio process to spawn.

`system/bin/godot-lsp` bridges the two — it connects to that port and pipes the
socket to its own stdin/stdout. `system/install.sh` installs it to
`~/.local/bin/godot-lsp`. The config entry is a normal custom server:

```jsonc
"lsp": {
  "godot": {
    "command": ["godot-lsp"],
    "extensions": [".gd"]
  }
}
```

Two limits worth knowing:

- **The editor must already be running** with that project open. Nothing starts
  Godot for you. With no listener the bridge prints one line to stderr and exits
  without writing to stdout, so the client ends up with no server rather than a
  corrupt stream.
- **The port is per-editor.** If a project changed Editor Settings → Network →
  Language Server → Remote Port, set `GODOT_LSP_PORT` (and `GODOT_LSP_HOST`) in
  the environment the client inherits.

Godot's server is per-editor rather than per-project, so two Godot projects open
at once share port 6005 and the bridge attaches to whichever editor owns it.

### Python virtualenvs

The built-in `pyright` spawn checks, in order, `$VIRTUAL_ENV`, then `<root>/.venv`,
then `<root>/venv`, and passes the discovered interpreter as `pythonPath`. It
roots at the nearest `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`,
`Pipfile`, or `pyrightconfig.json`.

`uv` projects need no extra config — `uv` writes `.venv`, which is detected. If a
repo keeps its environment somewhere else, override it explicitly:

```jsonc
"lsp": {
  "pyright": {
    "initialization": { "pythonPath": "/path/to/venv/bin/python" }
  }
}
```

### Adding a server

An object keeps built-ins enabled and overrides individual entries. Note that an
object entry **does not** restrict servers to the listed set — all built-ins stay
seeded, so silence an unwanted one with `disabled`:

```jsonc
"lsp": {
  "bash": { "disabled": true },
  "custom-lsp": {
    "command": ["custom-lsp-server", "--stdio"],
    "extensions": [".custom"]
  }
}
```

Custom servers must declare `extensions`; the runtime cannot infer them.

## Claude Code: no native LSP

Claude Code has **no `lsp` setting**. There is no equivalent of OpenCode's key in
`.claude/settings.json`, so no config line can be added to the Claude Code
harness. Do not add a dead `lsp` key "for symmetry" — it is silently ignored.

Diagnostics reach Claude Code by two other routes:

- **IDE connection** (`/ide`) — attaches to a VS Code or JetBrains extension and
  inherits that editor's diagnostics, diff views, and selection context. This is
  the supported path and needs no project config.
- **MCP bridge** — an MCP server such as `mcp-language-server` wraps a language
  server and exposes definitions and diagnostics as tools. This adds an `npx`
  dependency to the project and is opt-in per project, not a harness default.

The practical consequence: a project relying on LSP for accurate navigation gets
it under OpenCode automatically, and under Claude Code only when an IDE is
attached or a bridge is configured.
