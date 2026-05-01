# ------------------------------------------------------------------------------
# ~/.zshrc – Adwaita-AMOLED ZSH Theme
# GNOME Adwaita Dark adapted for AMOLED displays (pure #000000 background)
#
# Requires:
#   zsh-syntax-highlighting
#   zsh-autosuggestions
#
# Plugin paths below assume a distro package install. Adjust if using a plugin
# manager (Oh My Zsh, Antidote, etc.) — the ZSH_HIGHLIGHT_STYLES and
# ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE variables work regardless of how you load them.
# ------------------------------------------------------------------------------

# --- Prompt -------------------------------------------------------------------
# user   → blue    #387af2  (@accent)          5.23:1
# path   → magenta #c678dd  (Doom One compat)  7.13:1
# ok     → green   #0aeea0  (success_color)   13.75:1
# err    → red     #ff0000  (error_color)       5.25:1
PROMPT='%B%F{#387af2}%n%f %F{#c678dd}%~%f %(?.%B%F{#0aeea0}❯%f%b.%B%F{#ff0000}❯%f%b) '

# Set terminal title to user@host: path
precmd() {
    print -n "\e]0;%n@%m: %~\a"
}

# --- Plugins ------------------------------------------------------------------
# Adjust paths to match your distro or plugin manager
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

# --- zsh-autosuggestions ------------------------------------------------------
# #555555 — ~3.5:1 on #000000: ghost text, visible but clearly subordinate
# (theme border_color #2a2a2a is only ~1.3:1 — invisible on pure black)
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#555555'

# --- zsh-syntax-highlighting --------------------------------------------------
# Must be set AFTER sourcing the plugin.
#
# Palette (Adwaita-AMOLED):
#   @accent        #387af2   5.23:1    @accent_hover  #4a8cf5   6.36:1
#   error_color    #ff0000   5.25:1    success_color  #0aeea0  13.75:1
#   warning_color  #f1ac00  10.64:1   magenta        #c678dd   7.13:1
#   disabled_text  #c0c0c0  11.54:1   ghost_text     #555555   ~3.5:1

# Commands & executables
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#ff0000,bold'        # error_color   – unrecognised input
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=#ff0000'             # error_color   – if/for/while/etc.
ZSH_HIGHLIGHT_STYLES[precommand]='fg=#f1ac00,italic'         # warning_color – sudo/env/time
ZSH_HIGHLIGHT_STYLES[command]='fg=#0aeea0,bold'              # success_color – external commands
ZSH_HIGHLIGHT_STYLES[alias]='fg=#0aeea0'                     # success_color – aliases
ZSH_HIGHLIGHT_STYLES[function]='fg=#0aeea0,bold'             # success_color – shell functions
ZSH_HIGHLIGHT_STYLES[builtin]='fg=#4a8cf5'                   # accent_hover  – cd/echo/etc.
ZSH_HIGHLIGHT_STYLES[arg0]='fg=#0aeea0,bold'                 # success_color – command word

# Arguments & paths
ZSH_HIGHLIGHT_STYLES[path]='fg=#387af2,underline'            # accent        – existing paths
ZSH_HIGHLIGHT_STYLES[path_prefix]='fg=#387af2'               # accent        – partial path
ZSH_HIGHLIGHT_STYLES[globbing]='fg=#f1ac00,bold'             # warning_color – * ? ** etc.
ZSH_HIGHLIGHT_STYLES[history-expansion]='fg=#c678dd'         # magenta       – !! !$

# Strings & quoting
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#f1ac00'         # warning_color
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#f1ac00'         # warning_color
ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]='fg=#f1ac00'         # warning_color
ZSH_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#4a8cf5'           # accent_hover
ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]='fg=#0aeea0'  # success_color – $VAR in "…"
ZSH_HIGHLIGHT_STYLES[back-double-quoted-argument]='fg=#4a8cf5'    # accent_hover  – \x in "…"

# Operators & redirections
ZSH_HIGHLIGHT_STYLES[redirection]='fg=#f1ac00,bold'          # warning_color – > >> | etc.
ZSH_HIGHLIGHT_STYLES[commandseparator]='fg=#ff0000,bold'     # error_color   – ; & && ||
ZSH_HIGHLIGHT_STYLES[assign]='fg=#387af2'                    # accent        – VAR=value

# Brackets
ZSH_HIGHLIGHT_STYLES[bracket-error]='fg=#ff0000,bold'        # error_color   – mismatched
ZSH_HIGHLIGHT_STYLES[bracket-level-1]='fg=#f1ac00,bold'      # warning_color
ZSH_HIGHLIGHT_STYLES[bracket-level-2]='fg=#0aeea0,bold'      # success_color
ZSH_HIGHLIGHT_STYLES[bracket-level-3]='fg=#387af2,bold'      # accent

# Misc
ZSH_HIGHLIGHT_STYLES[comment]='fg=#555555'                   # ghost_text    – ~3.5:1, readable but subdued
ZSH_HIGHLIGHT_STYLES[suffix-alias]='fg=#4a8cf5,underline'    # accent_hover
ZSH_HIGHLIGHT_STYLES[named-fd]='fg=#c678dd'                  # magenta
