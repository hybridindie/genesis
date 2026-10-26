# 00-options.zsh — shell behaviour and cosmetic defaults (interactive only).

setopt autocd                # `src` instead of `cd src`
setopt interactive_comments  # comments after a prompt command
setopt no_beep
setopt no_flow_control       # free up Ctrl-S / Ctrl-Q
setopt notify                # report background job changes immediately
setopt multios               # `cmd >a >b` writes both
setopt extended_glob         # ^negation / (#i) patterns, used by the aliases below

# macOS BSD ls colouring. On Linux `LS_COLORS`/`dircolors` is usually provided by
# the distro, and eza is used for listings anyway (70-aliases.zsh).
if [[ $OSTYPE == darwin* ]]; then
  export CLICOLOR=1
  export LSCOLORS='Gxfxcxdxbxegedabagacad'
fi

# bat: syntax-highlighted man pages and a pager that keeps colours.
if (( $+commands[bat] )); then
  export BAT_PAGER='less -FRX'
  export MANPAGER="sh -c 'col -bx | bat -l man -p'"
fi
