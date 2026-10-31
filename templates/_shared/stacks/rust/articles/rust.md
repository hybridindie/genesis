---
read_when: "Writing or changing Rust code, Cargo manifests, or native extensions"
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust Conventions

## MUST

- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass before commit.
- Commit `Cargo.lock` for binaries and native extensions.
- No `unwrap()` / `expect()` on fallible input in library code; return
  `Result` with a typed error (`thiserror`). `expect` is fine for true
  invariants, with a message saying why it cannot fail.
- Every `unsafe` block has a `// SAFETY:` comment stating the invariant it
  relies on.
- Code across an FFI or GDExtension boundary never panics into the host;
  catch and convert to an error value.

## SHOULD

- Deterministic logic takes its seed and inputs as parameters; no global RNG.
- Property tests (`proptest`) for generators and parsers.
- Keep the public API small; `pub(crate)` by default.
