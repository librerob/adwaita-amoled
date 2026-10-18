PROMPT='%B%F{#f3c29e}%n%f %F{#d49bea}%~%f %(?.%B%F{#0aeea0}❯%f%b.%B%F{#ff7b7b}❯%f%b) '

# Set terminal title without replacing other precmd hooks.
autoload -Uz add-zsh-hook
_adwaita_amoled_title() {
    print -Pn '\e]0;%n@%m: %~\a'
}
add-zsh-hook precmd _adwaita_amoled_title

# --- Completion System --------------------------------------------------------
if [[ -o interactive ]] && (( ! ${+functions[compdef]} )); then
    autoload -Uz compinit && compinit
fi
zstyle ':completion:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu select=long
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}" 'di=1;34' 'ln=35' 'so=32' 'ex=1;32' 'bd=30;46' 'cd=30;43' 'su=30;41' 'sg=30;46' 'tw=30;42' 'ow=30;43'
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS} 'ma=0;30;44'
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' special-dirs true


ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#a0a0a0'

# Optional fast-syntax-highlighting styles. Source its plugin before this file.
# Declaring the array also makes the snippet safe when the plugin is absent.
typeset -gA FAST_HIGHLIGHT_STYLES

# Commands & executables
FAST_HIGHLIGHT_STYLES[unknown-token]='fg=#ff7b7b,bold'        # error red    — bad/unrecognized input
FAST_HIGHLIGHT_STYLES[reserved-word]='fg=#f3c29e'             # accent blue  — if/for/while/do/done
FAST_HIGHLIGHT_STYLES[precommand]='fg=#f1ac00,italic'         # yellow       — sudo/env/time/nice
FAST_HIGHLIGHT_STYLES[command]='fg=#0aeea0,bold'              # success green — external commands
FAST_HIGHLIGHT_STYLES[alias]='fg=#0aeea0'                     # success green — aliases
FAST_HIGHLIGHT_STYLES[function]='fg=#0aeea0,bold'             # success green — shell functions
FAST_HIGHLIGHT_STYLES[builtin]='fg=#f3c29e'                   # accent blue  — cd/echo/export/etc.
FAST_HIGHLIGHT_STYLES[arg0]='fg=#0aeea0,bold'                 # success green — the command word itself

# Arguments & paths
FAST_HIGHLIGHT_STYLES[path]='fg=#01c1f1,underline'            # cyan         — verified existing paths
FAST_HIGHLIGHT_STYLES[path_prefix]='fg=#01c1f1'               # cyan         — partial/incomplete path
FAST_HIGHLIGHT_STYLES[globbing]='fg=#f1ac00,bold'             # yellow       — * ? ** [...] etc.
FAST_HIGHLIGHT_STYLES[history-expansion]='fg=#d49bea'         # magenta      — !foo, !$, !!

# Strings & quoting
FAST_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#f1ac00'         # yellow  — 'literal string'
FAST_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#f1ac00'         # yellow  — "interpolated string"
FAST_HIGHLIGHT_STYLES[dollar-quoted-argument]='fg=#f1ac00'         # yellow  — $'...'
FAST_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#01c1f1'           # cyan    — `command substitution`
FAST_HIGHLIGHT_STYLES[dollar-double-quoted-argument]='fg=#0aeea0'  # green   — $VAR inside "..."
FAST_HIGHLIGHT_STYLES[back-double-quoted-argument]='fg=#01c1f1'    # cyan    — \x escape inside "..."

# Operators & redirections
FAST_HIGHLIGHT_STYLES[redirection]='fg=#f1ac00,bold'          # yellow       — > >> < 2>&1 etc.
FAST_HIGHLIGHT_STYLES[commandseparator]='fg=#ff7b7b,bold'     # error red    — ; & && || (high-impact ops)
FAST_HIGHLIGHT_STYLES[assign]='fg=#01c1f1'                    # cyan         — VAR=value

# Brackets — use distinct steps across the palette so nesting depth is clear
FAST_HIGHLIGHT_STYLES[bracket-error]='fg=#ff9a9a,bold'        # bright red   — mismatched brackets
FAST_HIGHLIGHT_STYLES[bracket-level-1]='fg=#ffcc44,bold'      # bright yellow
FAST_HIGHLIGHT_STYLES[bracket-level-2]='fg=#4affc4,bold'      # bright green
FAST_HIGHLIGHT_STYLES[bracket-level-3]='fg=#f5dccb,bold'      # accent hover blue

# Misc
FAST_HIGHLIGHT_STYLES[comment]='fg=#a0a0a0'                   # ghost        — shell comments (#...)
FAST_HIGHLIGHT_STYLES[suffix-alias]='fg=#01c1f1,underline'    # cyan         — suffix aliases (.py etc.)
FAST_HIGHLIGHT_STYLES[named-fd]='fg=#d49bea'                  # magenta      — named file descriptors
