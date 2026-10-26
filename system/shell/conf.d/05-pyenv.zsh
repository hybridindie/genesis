# 05-pyenv.zsh — pyenv shell integration (only when pyenv is installed).
#
# `zshenv` already puts pyenv's shims on PATH, so python/pip resolve in every
# shell without this file. What `pyenv init` adds is the `pyenv` shell wrapper
# (`pyenv shell|activate|rehash`) plus `PYENV_SHELL`, and
# `pyenv virtualenv-init` adds the precmd hook that auto-activates the
# virtualenv for a directory.
#
# Both commands are python startups (~20 ms + ~43 ms), so their generated shell
# code is cached and only regenerated when the pyenv binary changes. The cached
# script re-evaluates PATH at source time, so caching does not freeze PATH.

if (( $+commands[pyenv] )); then
  typeset _pyenv_cache="${XDG_CACHE_HOME}/zsh/pyenv-init.zsh"
  if [[ ! -s $_pyenv_cache || $commands[pyenv] -nt $_pyenv_cache ]]; then
    mkdir -p "${_pyenv_cache:h}"
    {
      command pyenv init - --no-rehash zsh
      command pyenv virtualenv-init - zsh
    } >| "$_pyenv_cache" 2>/dev/null || rm -f "$_pyenv_cache"
  fi
  [[ -s $_pyenv_cache ]] && source "$_pyenv_cache"
  unset _pyenv_cache

  # pyenv init prepends its shims ahead of ~/.local/bin. Keep the user's own
  # binaries first so a standalone uv/uvx in ~/.local/bin wins over copies
  # bundled inside a pyenv version (dedup keeps the first occurrence).
  path=("$HOME/.local/bin" "$HOME/.opencode/bin" $path)
  export PATH
fi
