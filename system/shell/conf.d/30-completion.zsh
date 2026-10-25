# 30-completion.zsh — completion styling and fzf-tab behaviour.

# Case-insensitive, then smarter partial matching (m:{a-z}={A-Za-z} etc.).
zstyle ':completion:*' matcher-list \
  'm:{a-z}={A-Za-z}' \
  'm:{a-zA-Z}={A-Za-z}' \
  'r:|[._-]=* r:|=*'

zstyle ':completion:*' menu no                    # fzf-tab owns the menu
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%F{yellow}%d%f'
zstyle ':completion:*' list-dirs-first true
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME}/zsh/compcache"
zstyle ':completion:*' verbose yes
zstyle ':completion:*:warnings' format '%F{red}no matches%f'

# Colours: macOS sets no LS_COLORS, so the old `list-colors ${(s.:.)LS_COLORS}`
# was a no-op. Use LS_COLORS when present, otherwise a small readable palette.
if [[ -n ${LS_COLORS:-} ]]; then
  zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
else
  zstyle ':completion:*' list-colors \
    'di=1;34' 'ln=1;36' 'ex=1;32' 'or=1;31' 'pi=33' 'so=1;35' 'bd=33;1' 'cd=33;1'
fi

# fzf-tab previews. These run only while an fzf menu is open, so they cost nothing
# at startup. eza/bat/ps/git are all guarded by the widget that needs them.
if (( $+commands[eza] )); then
  zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always --group-directories-first -- ${realpath:q}'
else
  zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls -1G ${realpath:q}'
fi
if (( $+commands[bat] )); then
  zstyle ':fzf-tab:complete:(cat|bat|less|more|head|tail|nvim|vim|vi|diff|cp|mv|ln|rm|chmod|open|rg|fd):*' \
    fzf-preview 'bat --style=numbers --color=always --line-range=:120 -- ${realpath:q}'
fi
zstyle ':fzf-tab:complete:(kill|ps):argument-rest' fzf-preview 'ps -p ${word:q} -o command='
zstyle ':fzf-tab:complete:git-(add|diff|restore|show|checkout):*' fzf-preview 'git diff --color=always -- ${realpath:q}'
zstyle ':fzf-tab:*' fzf-flags --height=60% --layout=reverse
zstyle ':fzf-tab:*' switch-group ',' '.'
zstyle ':fzf-tab:*' continuous-trigger '/'
