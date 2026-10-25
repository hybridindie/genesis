# 70-aliases.zsh — aliases and small helpers.
#
# Aliases that reference a missing binary are guarded, so a half-installed
# machine does not turn a typo into a confusing "command not found".

# ---- config ------------------------------------------------------------------
zshconfig() { ${=EDITOR} "$ZSHDIR" }   # EDITOR may contain args ("zed --wait")
alias reload='exec zsh -l'             # re-read the config in place

# ---- editing / navigation ----------------------------------------------------
alias c='clear'
alias vi='nvim'
alias vim='nvim'

# ---- listing ----------------------------------------------------------------
# eza replaces ls when installed. Note eza's `-h` is --help, not "human readable":
# use `ll`/`la` instead of `ls -lh`.
#
# eza 0.23 reads file names from stdin when it gets no path argument and stdin is
# not a tty, which makes `zsh -ic 'ls' </dev/null` print nothing. Pass `.`
# explicitly when only flags were given.
if (( $+commands[eza] )); then
  _eza_() {
    emulate -L zsh
    if (( $# == 0 || ${(M)#@:#-*} == $# )); then
      command eza "$@" .
    else
      command eza "$@"
    fi
  }
  alias ls='_eza_ --group-directories-first'
  alias ll='_eza_ -l --git --group-directories-first'
  alias la='_eza_ -la --git --group-directories-first'
  alias lt='_eza_ --tree --level=2 --git-ignore --group-directories-first'
  alias tree='_eza_ --tree --git-ignore --group-directories-first'
elif [[ $OSTYPE == darwin* ]]; then
  alias ls='ls -G'
  alias ll='ls -lGh'
  alias la='ls -lAGh'
else
  alias ls='ls --color=auto'
  alias ll='ls -lh'
  alias la='ls -lAh'
fi

# ---- tools -------------------------------------------------------------------
alias k='kubectl'
alias jq='jq -C'
alias jqp='jq -C .'
(( $+commands[yq] ))      && alias yqp='yq -C .'
(( $+commands[lazygit] )) && alias lg='lazygit'
(( $+commands[http] ))    && alias get='http --print=HBhb GET' \
                          && alias post='http --print=HBhb POST'

# ---- python ------------------------------------------------------------------
# Refuses to run `pip uninstall` with an empty package list (BSD xargs has no -r).
cleanpip() {
  emulate -L zsh
  local -a pkgs
  pkgs=(${(f)"$(pip list --format=freeze 2>/dev/null | cut -d= -f1 | grep -vE '^(pip|setuptools|wheel)$')"})
  (( $#pkgs )) || { print 'cleanpip: nothing to uninstall'; return 0 }
  pip uninstall -y $pkgs
}
