# 50-prompt.zsh — prompt.
#
# starship is cheap here (~5 ms) and the old config had no starship.toml, so the
# defaults are used. Add ~/.config/starship.toml to customise.
if [[ -o zle ]] && (( $+commands[starship] )); then
  eval "$(starship init zsh)"
fi
