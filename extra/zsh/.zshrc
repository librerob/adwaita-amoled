PROMPT='%B%F{#387af2}%n%f %F{#c678dd}%~%f %(?.%B%F{#0aeea0}❯%f%b.%B%F{#ff3333}❯%f%b) '

# Set terminal title
precmd() {
    print -n "\e]0;%n@%m: %~\a"
}

# --- Completion System --------------------------------------------------------
autoload -Uz compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu select=long
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}" 'di=1;34' 'ln=35' 'so=32' 'ex=1;32' 'bd=34;46' 'cd=34;43' 'su=30;41' 'sg=30;46' 'tw=30;42' 'ow=30;43'
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS} 'ma=1;37;44'
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' special-dirs true


ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#767676'

# Commands & executables
FAST_HIGHLIGHT_STYLES[unknown-token]='fg=#ff3333,bold'        # error red    — bad/unrecognized input
FAST_HIGHLIGHT_STYLES[reserved-word]='fg=#387af2'             # accent blue  — if/for/while/do/done
FAST_HIGHLIGHT_STYLES[precommand]='fg=#f1ac00,italic'         # yellow       — sudo/env/time/nice
FAST_HIGHLIGHT_STYLES[command]='fg=#0aeea0,bold'              # success green — external commands
FAST_HIGHLIGHT_STYLES[alias]='fg=#0aeea0'                     # success green — aliases
FAST_HIGHLIGHT_STYLES[function]='fg=#0aeea0,bold'             # success green — shell functions
FAST_HIGHLIGHT_STYLES[builtin]='fg=#387af2'                   # accent blue  — cd/echo/export/etc.
FAST_HIGHLIGHT_STYLES[arg0]='fg=#0aeea0,bold'                 # success green — the command word itself

# Arguments & paths
FAST_HIGHLIGHT_STYLES[path]='fg=#01c1f1,underline'            # cyan         — verified existing paths
FAST_HIGHLIGHT_STYLES[path_prefix]='fg=#01c1f1'               # cyan         — partial/incomplete path
FAST_HIGHLIGHT_STYLES[globbing]='fg=#f1ac00,bold'             # yellow       — * ? ** [...] etc.
FAST_HIGHLIGHT_STYLES[history-expansion]='fg=#c678dd'         # magenta      — !foo, !$, !!

# Strings & quoting
FAST_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#f1ac00'         # yellow  — 'literal string'
FAST_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#f1ac00'         # yellow  — "interpolated string"
FAST_HIGHLIGHT_STYLES[dollar-quoted-argument]='fg=#f1ac00'         # yellow  — $'...'
FAST_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#01c1f1'           # cyan    — `command substitution`
FAST_HIGHLIGHT_STYLES[dollar-double-quoted-argument]='fg=#0aeea0'  # green   — $VAR inside "..."
FAST_HIGHLIGHT_STYLES[back-double-quoted-argument]='fg=#01c1f1'    # cyan    — \x escape inside "..."

# Operators & redirections
FAST_HIGHLIGHT_STYLES[redirection]='fg=#f1ac00,bold'          # yellow       — > >> < 2>&1 etc.
FAST_HIGHLIGHT_STYLES[commandseparator]='fg=#ff3333,bold'     # error red    — ; & && || (high-impact ops)
FAST_HIGHLIGHT_STYLES[assign]='fg=#01c1f1'                    # cyan         — VAR=value

# Brackets — use distinct steps across the palette so nesting depth is clear
FAST_HIGHLIGHT_STYLES[bracket-error]='fg=#ff4444,bold'        # bright red   — mismatched brackets
FAST_HIGHLIGHT_STYLES[bracket-level-1]='fg=#ffcc44,bold'      # bright yellow
FAST_HIGHLIGHT_STYLES[bracket-level-2]='fg=#4affc4,bold'      # bright green
FAST_HIGHLIGHT_STYLES[bracket-level-3]='fg=#4a8cf5,bold'      # accent hover blue

# Misc
FAST_HIGHLIGHT_STYLES[comment]='fg=#767676'                   # ghost        — shell comments (#...)
FAST_HIGHLIGHT_STYLES[suffix-alias]='fg=#01c1f1,underline'    # cyan         — suffix aliases (.py etc.)
FAST_HIGHLIGHT_STYLES[named-fd]='fg=#c678dd'                  # magenta      — named file descriptors
