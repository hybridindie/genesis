# 20-plugins.zsh — zinit, plugins, generated completions, compinit.
#
# Load order matters:
#   1. anything that adds to `fpath`           (before compinit)
#   2. fzf-tab                                (binds Tab, before 40-keybindings)
#   3. compinit                               (cached dump)
#   4. turbo plugins                          (widget wrappers, at first prompt)

# ---- zinit (plugin manager) ---------------------------------------------------
ZINIT_HOME="${XDG_DATA_HOME}/zinit/zinit.git"
if [[ ! -d $ZINIT_HOME ]]; then
  print -u2 "zsh: installing zinit into $ZINIT_HOME"
  mkdir -p "${ZINIT_HOME:h}"
  git clone --depth 1 https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi
source "$ZINIT_HOME/zinit.zsh"

# ---- completions that must exist before compinit ------------------------------
zinit light zsh-users/zsh-completions

# fzf-tab binds ^I itself, so it has to load BEFORE 40-keybindings rebinds Tab
# to the partial-accept widget.
zinit light Aloxaf/fzf-tab

# Defines the widgets bound in 40-keybindings (↑/↓ prefix search).
zinit light zsh-users/zsh-history-substring-search

# fzf: Ctrl-R history, Ctrl-T files, Alt-C cd. Loaded here, *after* fzf-tab and
# *before* 40-keybindings, on purpose:
#   * fzf-completion remembers fzf-tab's Tab binding as its fallback, so the `**`
#     trigger works without clobbering the Tab binding installed later;
#   * the tty check keeps `zsh -i -c` (no terminal) silent: fzf's init restores
#     options with `setopt zle`, which fails when ZLE cannot be enabled.
if [[ -o zle && -t 0 ]] && (( $+commands[fzf] )); then
  # Use fd instead of fzf's built-in walker: it honours .gitignore and excludes
  # .git, so Ctrl-T / Alt-C stay usable in big repos. Previews only if the tools
  # exist (they are optional; see 70-aliases.zsh for the ls aliases).
  if (( $+commands[fd] )); then
    export FZF_CTRL_T_COMMAND='fd --type f --hidden --follow --exclude .git'
    export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
  fi
  (( $+commands[bat] )) && export FZF_CTRL_T_OPTS="--preview 'bat --style=numbers --color=always --line-range=:200 -- {}'"
  (( $+commands[eza] )) && export FZF_ALT_C_OPTS="--preview 'eza --tree --level=1 --color=always -- {}'"
  eval "$(fzf --zsh)"
fi

# OMZ snippets: aliases + git completions. Loaded synchronously because they add
# to fpath / call compdef and must be in place before compinit.
zinit snippet OMZP::git
zinit snippet OMZP::sudo
zinit snippet OMZP::kubectl      # aliases (kgp/kgs/kd/...); the completion function
                                 # comes from the newer generated _kubectl below
zinit snippet OMZP::python       # py/pyclean/pyfind utilities
zinit snippet OMZP::pip
# dropped: OMZP::command-not-found (macOS has no apt; 80-agents.zsh implements a
# better handler) and OMZP::kubectx (kubectx/kubens binaries are not installed).

# ---- generated completions for CLIs that ship their own ----------------------
# Cached under ~/.cache/zsh and regenerated only when the binary is newer than the
# cache file, so this costs nothing on a normal startup.
_zsh_cache_completion() {
  local cmd=$1 out="${XDG_CACHE_HOME}/zsh/completions/_$1" tmp
  shift
  (( $+commands[$cmd] )) || return 0
  if [[ ! -s $out || $commands[$cmd] -nt $out ]]; then
    tmp="$out.tmp"
    # Validate the output: a wrong shell argument (e.g. `gh completion zsh`)
    # silently emits *bash* completion, which compinit ignores.
    if "$cmd" "$@" zsh >| "$tmp" 2>/dev/null && head -n 5 "$tmp" | grep -q '^#compdef'; then
      mv -f "$tmp" "$out"
    else
      rm -f "$tmp" "$out"
    fi
  fi
  [[ -s $out ]] && fpath=("${out:h}" $fpath)
}

# The completion cache directory is not created anywhere else — compinit below
# only creates its parent. Without it the redirects above fail on a fresh home
# with "no such file or directory: .../_gh.tmp" and no completion is cached.
mkdir -p "${XDG_CACHE_HOME}/zsh/completions"

_zsh_cache_completion kubectl completion
_zsh_cache_completion gh      completion -s
_zsh_cache_completion docker  completion
_zsh_cache_completion opencode --completions
_zsh_cache_completion herdr   completion
unset -f _zsh_cache_completion

# User-supplied completions (kept from the old config; may be empty).
[[ -d $HOME/.zfunc ]] && fpath=("$HOME/.zfunc" $fpath)

# ---- compinit: cached dump, full rebuild at most once a day ------------------
autoload -Uz compinit
_ZCOMPDUMP="${XDG_CACHE_HOME}/zsh/zcompdump-${HOST}-${ZSH_VERSION}"
mkdir -p "${_ZCOMPDUMP:h}"

# Rebuild the dump when it is stale (>24h) OR when a generated completion file is
# newer than it — otherwise a freshly generated _gh would be ignored until the
# next daily rebuild.
#
# NOTE: `[[ -n $file(#qN.mh+24) ]]` (the idiom this config used before) does NOT
# evaluate glob qualifiers inside `[[ ]]`: it is simply a non-empty string test,
# so the old config ran a full ~200 ms compinit on every shell. Expand into an
# array instead — that applies the qualifier properly.
typeset -a _stale
_stale=($_ZCOMPDUMP(N.mh+24))
_need_full=0
(( $#_stale )) && _need_full=1
if (( ! _need_full )); then
  for _f in "${XDG_CACHE_HOME}"/zsh/completions/*(N); do
    [[ $_f -nt $_ZCOMPDUMP ]] && { _need_full=1; break }
  done
fi

if (( _need_full )); then
  # compinit's own up-to-date heuristic can still skip the rescan even with `-d`,
  # so remove the dump first to guarantee a rebuild.
  rm -f "$_ZCOMPDUMP"
  compinit -d "$_ZCOMPDUMP"       # stale: ~200 ms, at most once a day
else
  compinit -C -d "$_ZCOMPDUMP"    # fresh: ~20 ms
fi
unset _ZCOMPDUMP _need_full _f _stale

# ---- deferred plugins (turbo mode: loaded at the first prompt) ---------------
# These only wrap zle widgets; nothing before the first prompt needs them, and
# deferring them keeps the shell feeling instant.
zinit wait lucid light-mode for \
  zsh-users/zsh-autosuggestions \
  zsh-users/zsh-syntax-highlighting

# ---- plugin settings (read when the deferred plugins load) -------------------
# fish-style inline suggestion from history. Tab/partial accept is implemented in
# 40-keybindings.zsh; Ctrl+Space accepts the whole suggestion.
ZSH_AUTOSUGGEST_STRATEGY=(history)
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=8'
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=200
ZSH_AUTOSUGGEST_HISTORY_IGNORE='?(#c0,1)'

HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='bg=magenta,fg=white,bold'
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='bg=red,fg=white,bold'
HISTORY_SUBSTRING_SEARCH_PREFIXED=1

zinit cdreplay -q
