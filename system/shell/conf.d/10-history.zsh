# 10-history.zsh — history storage and sharing.
#
# The old config used `hist_ignore_all_dups` with HISTSIZE=5000 and produced a
# 293-line history file after months of use: it erases older copies of every
# repeated command, which also starves zsh-autosuggestions. `hist_ignore_dups`
# removes only *consecutive* duplicates and keeps the rest.

HISTSIZE=200000
SAVEHIST=200000
HISTFILE="$HOME/.zsh_history"   # classic path: fzf/atuin/other tools read it

setopt extended_history      # timestamps + command duration
setopt share_history         # live sharing between panes (implies inc_append_history)
setopt hist_ignore_space     # a leading space keeps a command out of history (secrets)
setopt hist_ignore_dups      # collapse consecutive duplicates
setopt hist_expire_dups_first
setopt hist_reduce_blanks    # squeeze runs of whitespace
setopt hist_verify           # show the expanded command before running it
