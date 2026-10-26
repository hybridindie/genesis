# 40-keybindings.zsh — ZLE keymaps.
#
# Skipped when ZLE is unavailable (`zsh -i -c`, scripts, CI) so those shells stay
# silent and fast.

[[ -o zle ]] || return 0

bindkey -e

# ---- history ----------------------------------------------------------------
bindkey '^p' history-search-backward          # prefix search, kept from the old config
bindkey '^n' history-search-forward
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
[[ -n ${terminfo[kcuu1]:-} ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
[[ -n ${terminfo[kcud1]:-} ]] && bindkey "$terminfo[kcud1]" history-substring-search-down

# ---- suggestions ------------------------------------------------------------
# Accept the whole visible suggestion.
_accept_suggestion() {
  if [[ -n $POSTDISPLAY ]] && (( $+widgets[autosuggest-accept] )); then
    zle autosuggest-accept
  else
    zle end-of-line
  fi
}
zle -N _accept_suggestion

# Accept ONE word of the suggestion, then fall back to normal completion.
#
#   suggestion: kubectl apply -f path/to/file.yml
#     Tab          -> kubectl
#     Tab          -> kubectl apply
#     Tab          -> kubectl apply -f
#     Ctrl+Space   -> the whole suggestion
#
# zsh-autosuggestions only shows a suggestion that continues what you already
# typed, so accepting a word is always safe. When nothing is suggested, Tab opens
# the usual fzf-tab completion menu.
_tab_smart() {
  emulate -L zsh
  if [[ -n $POSTDISPLAY && -n $LBUFFER ]]; then
    local consumed
    if [[ $POSTDISPLAY =~ '^([[:space:]]*[^[:space:]]+)' ]]; then
      consumed=$match[1]
      LBUFFER+=$consumed
      POSTDISPLAY=${POSTDISPLAY#$consumed}
      if (( $+widgets[autosuggest-fetch] )); then
        zle autosuggest-fetch       # recompute the remaining suggestion
      else
        POSTDISPLAY=
      fi
      return 0
    fi
  fi

  # fzf-completion keeps the `**` walk trigger and delegates to fzf-tab-complete
  # otherwise; fall back to the plain completion widget if fzf is absent.
  if (( $+widgets[fzf-completion] )); then
    zle fzf-completion
  elif (( $+widgets[fzf-tab-complete] )); then
    zle fzf-tab-complete
  else
    zle expand-or-complete
  fi
}
zle -N _tab_smart

bindkey '^I'      _tab_smart            # Tab: next word of the suggestion, else completions
bindkey '^@'      _accept_suggestion    # Ctrl+Space: whole suggestion
bindkey '^[[1;5C' forward-word          # Ctrl+Right: next word (autosuggestions wraps this)
bindkey '^[[1;3C' forward-word          # Alt+Right: next word
bindkey '^[[Z'    reverse-menu-complete # Shift+Tab: step backwards through completions
