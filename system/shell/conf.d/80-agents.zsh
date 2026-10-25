# 80-agents.zsh — helpers for working with AI agents from the shell.

# ---- assistant helpers -------------------------------------------------------
#   ?? how do I list only directories with ls
#   ?sh rename every .jpeg here to .jpg
#
# The backend defaults to `opencode run`; override it without editing this file:
#   export LLM_SHELL_CMD='claude -p'
#
# `??`/`?sh` are aliases, not function names: a function called `??` would be
# glob-expanded (two-character filename pattern) before zsh resolves the command,
# so typing it at the prompt fails with "no matches found".
: ${LLM_SHELL_CMD:='opencode run'}

# A few lines of context so answers refer to this directory, repo and last command.
_shell_context() {
  emulate -L zsh
  local ctx="cwd: $PWD"$'\n'"shell: $SHELL on $OSTYPE"
  local branch
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  [[ -n $branch ]] && ctx+=$'\n'"git branch: $branch"
  local last
  last=$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')
  # Quoted patterns are literal: unquoted `??` in a zsh pattern means "any two
  # characters", which would match every command and drop the context line.
  case $last in
    ''|'??'*|'?sh'*|*_ask_assistant*|*_ask_shell_cmd*) ;;
    *) ctx+=$'\n'"last command: $last" ;;
  esac
  print -r -- "$ctx"
}

_ask_assistant() {
  emulate -L zsh
  (( $# )) || { print -u2 'usage: ?? <question>'; return 2 }
  print -u2 "… asking ${LLM_SHELL_CMD%% *}"
  ${=LLM_SHELL_CMD} \
    "You are answering a question typed at a developer's shell prompt. Be brief and concrete. Target ${OSTYPE} with a POSIX shell and the tools that exist there."$'\n\n'"$(_shell_context)"$'\n\n'"Q: $*"
}

_ask_shell_cmd() {
  emulate -L zsh
  (( $# )) || { print -u2 'usage: ?sh <task>'; return 2 }
  ${=LLM_SHELL_CMD} \
    "Reply with exactly one shell command that accomplishes the task. No explanation, no markdown, no surrounding backticks. Target ${OSTYPE}, using portable POSIX tools unless the task needs something else."$'\n\n'"task: $*"
}

alias '??'='_ask_assistant'
alias '?sh'='_ask_shell_cmd'

# ---- command not found -------------------------------------------------------
# Fast and offline: it only prints hints; nothing is executed, no network.
command_not_found_handler() {
  if [[ $1 == */* ]]; then
    print -u2 "zsh: no such file or directory: $1"
    return 127
  fi
  print -u2 "zsh: command not found: $1"
  if (( $+commands[brew] )); then
    print -u2 "  hint: brew search $1            # look for a package"
  elif (( $+commands[apt] )); then
    print -u2 "  hint: apt search $1             # look for a package"
  elif (( $+commands[dnf] )); then
    print -u2 "  hint: dnf search $1             # look for a package"
  elif (( $+commands[pacman] )); then
    print -u2 "  hint: pacman -Ss $1             # look for a package"
  fi
  (( $+commands[uv] )) && print -u2 "  hint: uv tool install <name>    # python CLI"
  print -u2 "  hint: ?? what provides $1 on $OSTYPE"
  return 127
}

# ---- herdr (only inside a herdr-managed pane) --------------------------------
if [[ ${HERDR_ENV:-0} == 1 ]] && (( $+commands[herdr] )); then
  alias hst='herdr status'
  alias hag='herdr agent list'
  alias hpn='herdr pane list'
  alias hws='herdr workspace list'

  # Run a long command and raise a herdr notification when it finishes.
  hnotify() {
    (( $# )) || { print -u2 'usage: hnotify <command ...>'; return 2 }
    "$@"
    local rc=$?
    local sound=done
    (( rc )) && sound=request
    herdr notification show "done: ${(j: :)${(q)@}}" \
      --body "exit $rc · ${PWD:t}" --sound $sound 2>/dev/null
    return $rc
  }
fi
