# 60-integrations.zsh — direnv, zoxide, and the cd wrapper.
#
# fzf is initialised in 20-plugins.zsh (it must load before the Tab binding in
# 40-keybindings.zsh, which has to be the final word on ^I).

# direnv: per-directory environment from .envrc (auto load/unload on cd).
if (( $+commands[direnv] )); then
  # Silence "direnv: loading/unloading ..." on every cd: it lands on stderr and
  # pollutes output captured by agents and scripts. Errors are still reported.
  export DIRENV_LOG_FORMAT=''
  eval "$(direnv hook zsh)"
fi

# zoxide — must stay the last integration init so its chpwd hook is not displaced.
if (( $+commands[zoxide] )); then
  eval "$(zoxide init --cmd cd zsh)"

  # Self-heal: re-register zoxide's chpwd hook if something displaced it. Agent
  # tooling (e.g. Claude Code shell snapshots) restores functions but not shell
  # arrays such as chpwd_functions, which silently breaks `cd` ranking.
  # Defined only when zoxide is present: `__zoxide_z` does not exist otherwise.
  function cd() {
    (( ${+functions[__zoxide_hook]} )) &&
      [[ ${chpwd_functions[(Ie)__zoxide_hook]:-0} -eq 0 ]] &&
      chpwd_functions+=(__zoxide_hook)
    __zoxide_z "$@"
  }
fi
