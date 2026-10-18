#!/usr/bin/env bash
# Install the compiled theme directly. No Python, saved state or backup database.
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
THEME=Adwaita-AMOLED
ACCENT=auto
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
CONFIG=${XDG_CONFIG_HOME:-$HOME/.config}
DESKTOP=${XDG_CURRENT_DESKTOP:-}
DEST=$DATA/themes
LIBADWAITA=false ACTIVATE=false SHELL_THEME=false SYSTEM=false REMOVE=false DRY_RUN=false
GUIDED=false
CUSTOM_DEST=false GTK_MODE=auto SHELL_VERSION=auto
LINK_PARENT=''
EXTRAS=() FLATPAKS=() TARGETS=()
PAYLOAD=()
ACCENT_PAYLOAD=()
declare -A ACCENT_OVERRIDES=()
REQUIRED=(accent-name index.theme gtk-2.0/gtkrc gtk-3.0/gtk.css gtk-3.0/gtk.gresource
          gtk-4.0/gtk.css gtk-4.0/gtk.gresource cinnamon/cinnamon.css
          metacity-1/metacity-theme-3.xml openbox-3/themerc
          gnome-shell/gnome-shell-46.css gnome-shell/gnome-shell-51.css
          extra/libadwaita/gtk.css extra/libadwaita/gtk-modern.css
          extra/libadwaita/gtk-dark.css extra/libadwaita/libadwaita-tweaks.css)

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Run without options in a terminal for guided setup. Explicit options never prompt.
Install the included theme. Rerun to overwrite/update it; no backups or state.
Default destination: ${XDG_DATA_HOME:-$HOME/.local/share}/themes/Adwaita-AMOLED

  -l, --libadwaita          Replace native GTK4 override files with theme links
  -a, --activate            Select the theme for the current desktop
      --accent COLOR        blue, yellow, gold, purple, green, red, orange, pink
                            Default: keep installed color, or blue for a new install
      --shell               Require a matching GNOME Shell theme (46 or 51)
      --extras LIST         Copy optional themes: qt,kitty,alacritty,bat,nvim,
                            rofi,zsh,wallpaper or all (select them in each app)
      --flatpak ID=MODE     Configure one app; MODE is legacy, modern or gtk3
      --gtk4-mode MODE      Native GTK4: auto, legacy (<4.16), modern (4.16+)
      --shell-version VER   auto, 46 or 51
  -d, --dest DIR            Theme parent directory
      --system              Install for all users in /usr/local/share/themes
      --link DIR            Link DIR/Adwaita-AMOLED to the system copy (root only)
  -r, --remove              Remove the theme, its native GTK4 links and selected extras
      --dry-run             Print operations without changing files/settings
      --interactive         Open guided setup (terminal required; use alone)
  -h, --help                Show this help

Examples:
  ./install.sh
  ./install.sh -l --activate
  ./install.sh --extras qt,kitty
  sudo ./install.sh --system
  sudo ./install.sh --system --link /usr/share/themes

GTK4 linking replaces gtk.css, gtk-dark.css, libadwaita-tweaks.css and assets
under the selected gtk-4.0 config directory. No backup is created.
Existing Git checkouts and unlisted local files block theme replacement/removal.
Move them outside the installation destination first; known theme files are replaced.
Native GTK4 removal unlinks only links pointing into this theme; custom CSS stays.
App themes are copied without rewriting your .zshrc, init.lua or other settings.
User installation sets supported application appearance preferences to dark.
Unavailable or locked appearance settings are skipped; system/removal leave them alone.
EOF
}

installed_accent() {
    local name=blue
    if [[ -f $1/accent-name && ! -L $1/accent-name ]]; then IFS= read -r name < "$1/accent-name" || :; fi
    case $name in blue|yellow|gold|purple|green|red|orange|pink) printf '%s\n' "$name" ;; *) printf 'blue\n' ;; esac
}

# GTK theme selection and the portal's app appearance preference are separate.
# Non-GNOME sessions may use either the GTK or XApp settings portal. Configure
# their available keys together; the guided review lists each one explicitly.
dark_preference_settings() {
    local schema range writable
    local -a candidates=() dark_schemas=()
    command -v gsettings >/dev/null || { printf 'gsettings is unavailable.\n' >&2; return 1; }
    case ${DESKTOP^^} in
        *CINNAMON*|*MATE*|*XFCE*) candidates=(org.x.apps.portal org.gnome.desktop.interface) ;;
        *GNOME*|*BUDGIE*) candidates=(org.gnome.desktop.interface) ;;
        *) printf 'No supported dark-appearance setting for this desktop.\n' >&2; return 1 ;;
    esac
    for schema in "${candidates[@]}"; do
        range=$(gsettings range "$schema" color-scheme 2>/dev/null) || continue
        [[ $range == enum$'\n'* && $range == *"'prefer-dark'"* ]] || continue
        if ! gsettings get "$schema" color-scheme >/dev/null 2>&1; then
            printf 'Skipping unreadable app appearance setting: %s color-scheme\n' "$schema" >&2
            continue
        fi
        writable=$(gsettings writable "$schema" color-scheme) || writable=false
        [[ $writable == true ]] || {
            printf 'Skipping locked or unavailable app appearance setting: %s color-scheme\n' "$schema" >&2
            continue
        }
        dark_schemas+=("$schema")
    done
    ((${#dark_schemas[@]})) || { printf 'No supported writable app appearance key is available.\n' >&2; return 1; }
    printf '%s\n' "${dark_schemas[@]}"
}

if [[ ${1:-} == --interactive ]] || { (($# == 0)) && [[ -t 0 && -t 1 ]]; }; then
    [[ $# -le 1 ]] || die 'Use --interactive by itself, or pass regular options without it.'
    [[ -t 0 && -t 1 ]] || die 'Guided setup needs a terminal. Use --help for non-interactive options.'
    [[ -f $ROOT/setup-menu.sh ]] || die 'Incomplete theme download: setup-menu.sh is missing.'
    # shellcheck source=setup-menu.sh
    source "$ROOT/setup-menu.sh"
    GUIDED=true
    guided_setup
    set -- "${MENU_ARGS[@]}"
fi

value() { [[ $# -ge 2 && -n $2 && $2 != -* ]] || die "$1 needs a value"; }
components() {
    local item
    local -a items
    IFS=, read -r -a items <<< "$1"
    for item in "${items[@]}"; do
        case "$item" in
            gtk) ;;
            libadwaita) LIBADWAITA=true ;;
            shell) SHELL_THEME=true ;;
            all) LIBADWAITA=true; SHELL_THEME=true; EXTRAS+=(all) ;;
            *) EXTRAS+=("$item") ;;
        esac
    done
}
while (($#)); do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -l|--libadwaita) LIBADWAITA=true ;;
        -a|--activate) ACTIVATE=true ;;
        --accent) value "$@"; ACCENT=$2; shift ;;
        --prefer-dark) ;; # Accepted for v1.6.0 command compatibility; now the user-install default.
        --shell) SHELL_THEME=true ;;
        --system) SYSTEM=true ;;
        --link) value "$@"; LINK_PARENT=$2; shift ;;
        -r|-u|--remove|--uninstall|uninstall) REMOVE=true ;;
        --dry-run) DRY_RUN=true ;;
        -d|--dest) value "$@"; DEST=$2; CUSTOM_DEST=true; shift ;;
        --gtk4-mode) value "$@"; GTK_MODE=$2; shift ;;
        --shell-version) value "$@"; SHELL_VERSION=$2; shift ;;
        --flatpak) value "$@"; FLATPAKS+=("$2"); shift ;;
        --extras) value "$@"; IFS=, read -r -a items <<< "$2"; EXTRAS+=("${items[@]}"); shift ;;
        --components) value "$@"; components "$2"; shift ;;
        install|update|--yes) ;; # Accept the previous install/update spelling.
        *) die "Unknown option: $1. See --help." ;;
    esac
    shift
done

for tool in realpath rm mkdir cp ln chmod mv mktemp flock stat; do
    command -v "$tool" >/dev/null || die "Required Linux tool is missing: $tool"
done
[[ $GTK_MODE =~ ^(auto|legacy|modern)$ ]] || die 'GTK4 mode must be auto, legacy or modern.'
[[ $SHELL_VERSION =~ ^(auto|46|51)$ ]] || die 'Shell version must be auto, 46 or 51.'
case $ACCENT in auto|blue|yellow|gold|purple|green|red|orange|pink) ;; *) die 'Unknown accent color. Use blue, yellow, gold, purple, green, red, orange or pink.' ;; esac
if $SYSTEM; then
    ((EUID == 0)) || die 'Use sudo with --system.'
    $CUSTOM_DEST || DEST=/usr/local/share/themes
    if $LIBADWAITA || $ACTIVATE || (("${#EXTRAS[@]}" || "${#FLATPAKS[@]}")); then
        die '--system copies only the shared theme. Run user configuration separately without sudo.'
    fi
elif [[ -n ${SUDO_USER:-} ]]; then
    die 'Run user setup without sudo, or use --system for shared theme files.'
fi
[[ -z $LINK_PARENT ]] || $SYSTEM || die '--link requires --system; it must point to a root-owned copy, not a user theme.'
for path in "$HOME" "$DATA" "$CONFIG" "$DEST" ${LINK_PARENT:+"$LINK_PARENT"}; do
    [[ $path == /* && $path != / && $path != *$'\n'* ]] || die "Expected an absolute directory other than /: $path"
done
DEST=$(realpath -m -- "$DEST")
TARGET=$DEST/$THEME
[[ $ACCENT != auto ]] || ACCENT=$(installed_accent "$TARGET")
LINK_PATH=''
GTK2_LINK=''
if [[ -n $LINK_PARENT ]]; then
    LINK_PARENT=$(realpath -m -- "$LINK_PARENT")
    LINK_PATH=$LINK_PARENT/$THEME
    [[ $LINK_PATH != "$TARGET" ]] || die 'The shared link and system theme must use different parents.'
    if [[ -L $LINK_PATH ]]; then
        [[ $(stat -c %u -- "$LINK_PATH") == 0 ]] || die "Existing shared link is not root-owned: $LINK_PATH"
        [[ $(realpath -m -- "$LINK_PATH") == "$TARGET" ]] || die "Shared link already points elsewhere: $LINK_PATH"
    elif [[ -e $LINK_PATH ]]; then
        die "Shared link destination already exists: $LINK_PATH. Use --system --dest $LINK_PARENT to update a real theme directory there instead."
    fi
    # Root applications must not follow a link through a user-writable parent.
    for parent in "$DEST" "$LINK_PARENT"; do
        while [[ $parent != / ]]; do
            if [[ -e $parent ]]; then
                [[ $(stat -c %u -- "$parent") == 0 ]] || die "Shared theme/link parent is not root-owned: $parent"
                permissions=$(stat -c %a -- "$parent")
                (( (8#$permissions & 0022) == 0 || (8#$permissions & 01000) != 0 )) || die "Shared theme/link parent is writable by other users: $parent"
            fi
            parent=${parent%/*}; parent=${parent:-/}
        done
    done
fi
TARGETS+=("$TARGET")
# Refresh a legacy user copy too, so it cannot shadow the updated XDG copy.
if ! $SYSTEM && ! $CUSTOM_DEST && [[ -d $HOME/.themes/$THEME && ! -L $HOME/.themes/$THEME ]]; then
    legacy=$(realpath -m -- "$HOME/.themes/$THEME")
    [[ $legacy == "$TARGET" ]] || TARGETS+=("$legacy")
fi
# GTK2 searches ~/.themes, not XDG_DATA_HOME/themes. Keep one runtime copy,
# exposing it through a compatibility link only for the default user scope.
if ! $SYSTEM && ! $CUSTOM_DEST && { ! $REMOVE || ((${#FLATPAKS[@]} == 0)); }; then
    legacy_parent=$(realpath -m -- "$HOME/.themes")
    legacy_path=$legacy_parent/$THEME
    if [[ $legacy_path != "$TARGET" ]] && [[ ! -d $legacy_path || -L $legacy_path ]]; then
        if [[ -L $legacy_path && $(realpath -m -- "$legacy_path") != "$TARGET" ]]; then
            die "GTK2 theme path points elsewhere; keeping it unchanged: $legacy_path. Select its real parent with --dest."
        fi
        [[ ! -e $legacy_path || -L $legacy_path ]] || die "GTK2 theme path is not a directory: $legacy_path"
        [[ $legacy_path != "$TARGET/"* && $TARGET != "$legacy_path/"* ]] || die 'GTK2 compatibility path overlaps the installed theme.'
        [[ $legacy_path != "$ROOT" && $legacy_path != "$ROOT/"* ]] || die 'GTK2 compatibility path overlaps the source download.'
        GTK2_LINK=$legacy_path
    fi
fi
for target in "${TARGETS[@]}"; do
    [[ $ROOT != "$target" && $ROOT != "$target/"* && $target != "$ROOT/"* ]] ||
        die 'Run the installer from a separate extracted download or checkout, outside the installed theme.'
    [[ ! -L $target ]] || die "Theme destination is a symlink; select its real parent with --dest: $target"
done

run() {
    if $DRY_RUN; then printf '  '; printf '%q ' "$@"; printf '\n'; else "$@"; fi
}
copy_file() { run mkdir -p -- "$(dirname -- "$2")"; run cp --remove-destination -T -- "$1" "$2"; }
link_file() { run mkdir -p -- "$(dirname -- "$2")"; run rm -rf -- "$2"; run ln -s -- "$1" "$2"; }
remove_link() {
    local dest=$1 resolved
    [[ -L $dest ]] || return 0
    resolved=$(realpath -m -- "$dest")
    [[ $resolved == "$TARGET/"* ]] && run rm -f -- "$dest"
    return 0
}

# A theme update may replace known theme files, never a checkout or unrelated
# local data. Include the installed manifest so obsolete runtime assets from an
# older release can still be refreshed/removed without blocking normal updates.
check_existing_theme() (
    local target=$1 manifest name parent directory path relative
    local -a pending=("$target")
    local -A known_paths=([ARCHIVE_CONTENTS.sha256]=1) known_directories=()
    [[ -e $target ]] || return 0
    [[ -d $target ]] || die "Theme destination is not a directory: $target"
    [[ ! -e $target/.git && ! -L $target/.git ]] || die "Keeping Git checkout unchanged: $target. Move it outside the installation destination first."
    [[ -f $ROOT/runtime-files.txt ]] || die 'Incomplete installer download: runtime-files.txt is missing.'
    for manifest in "$ROOT/runtime-files.txt" "$target/runtime-files.txt"; do
        [[ ! -L $manifest ]] || die "Keeping linked runtime manifest unchanged: $manifest"
        [[ -f $manifest ]] || continue
        [[ -r $manifest ]] || die "Cannot read installed runtime manifest: $manifest"
        while IFS= read -r name || [[ -n $name ]]; do
            [[ $name =~ ^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$ && /$name/ != *'/../'* && /$name/ != *'/./'* && /$name/ != *'/.git/'* ]] || die "Invalid runtime path; keeping installed files: $manifest"
            known_paths[$name]=1
            parent=$name
            while [[ $parent == */* ]]; do parent=${parent%/*}; known_directories[$parent]=1; done
        done < "$manifest"
    done
    shopt -s dotglob nullglob
    while ((${#pending[@]})); do
        directory=${pending[-1]}; unset 'pending[-1]'
        [[ -r $directory && -x $directory ]] || die "Cannot inspect installed directory; keeping it unchanged: $directory"
        for path in "$directory"/*; do
            relative=${path#"$target/"}
            if [[ -d $path && ! -L $path ]]; then
                [[ ${known_directories[$relative]+yes} ]] || die "Keeping local directory unchanged: $path. Move it outside the theme before updating/removing."
                pending+=("$path")
            else
                [[ ${known_paths[$relative]+yes} || ( -L $path && ${known_directories[$relative]+yes} ) ]] || die "Keeping local file unchanged: $path. Move it outside the theme before updating/removing."
            fi
        done
    done
)

# A directory descriptor lock leaves no lock file or saved installation state.
lock_parent() {
    local parent=$1 fd
    [[ -d $parent ]] || return 0
    exec {fd}<"$parent"
    flock -n "$fd" || die "Another installer is using this destination: $parent"
}

validate_runtime() {
    local directory=$1 name
    for name in "${REQUIRED[@]}"; do
        [[ -f $directory/$name && -r $directory/$name && -s $directory/$name ]] || die "Incomplete theme download: $name is missing, empty or unreadable."
    done
    if [[ -f $ROOT/ARCHIVE_CONTENTS.sha256 ]]; then
        (cd -- "$directory" && sha256sum --check --status "$ROOT/ARCHIVE_CONTENTS.sha256") || die 'Archive checksum verification failed. Extract a complete, unmodified release archive.'
    fi
}

read_runtime_files() {
    local name parent
    local -A seen=()
    [[ -f $ROOT/runtime-files.txt ]] || die 'Incomplete theme download: runtime-files.txt is missing.'
    while IFS= read -r name || [[ -n $name ]]; do
        [[ $name =~ ^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$ && /$name/ != *'/../'* && /$name/ != *'/./'* ]] || die "Invalid runtime path: $name"
        [[ ! ${seen[$name]+present} ]] || die "Duplicate runtime path: $name"
        seen[$name]=1
        [[ -f $ROOT/$name && -r $ROOT/$name ]] || die "Incomplete theme download: $name is missing or unreadable."
        parent=$name
        while [[ -n $parent ]]; do
            [[ ! -L $ROOT/$parent ]] || die "Linked runtime path is not supported: $parent"
            if [[ $parent == */* ]]; then parent=${parent%/*}; else parent=''; fi
        done
        PAYLOAD+=("$name")
    done < "$ROOT/runtime-files.txt"
    [[ ${seen[runtime-files.txt]+present} ]] || die 'Runtime list must include runtime-files.txt.'
    for name in "${REQUIRED[@]}" install.sh setup-menu.sh INSTALLING.md; do
        [[ ${seen[$name]+present} ]] || die "Incomplete runtime file list: $name"
    done
}

read_accent_files() {
    local directory=$ROOT/accents/$ACCENT digest name parent
    local -A permitted=() seen=()
    for name in "${PAYLOAD[@]}"; do permitted[$name]=1; done
    [[ -f $directory/SHA256SUMS && ! -L $ROOT/accents && ! -L $directory && ! -L $directory/SHA256SUMS ]] || die "Incomplete accent download: $ACCENT"
    while read -r digest name || [[ -n $digest || -n $name ]]; do
        [[ $digest =~ ^[0-9a-f]{64}$ && $name =~ ^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$ && /$name/ != *'/../'* && /$name/ != *'/./'* ]] || die 'Invalid accent manifest.'
        [[ ${permitted[$name]+yes} && ! ${seen[$name]+yes} ]] || die "Unexpected or duplicate accent path: $name"
        seen[$name]=1
        ACCENT_OVERRIDES[$name]=1
        parent=$name
        while [[ -n $parent ]]; do
            [[ ! -L $directory/$parent ]] || die "Linked accent path is not supported: $parent"
            if [[ $parent == */* ]]; then parent=${parent%/*}; else parent=''; fi
        done
        [[ -f $directory/$name && -r $directory/$name ]] || die "Missing accent file: $name"
        ACCENT_PAYLOAD+=("$name")
    done < "$directory/SHA256SUMS"
    [[ ${seen[accent-name]+yes} && $(installed_accent "$directory") == "$ACCENT" ]] || die 'Accent identity is missing or incorrect.'
    (cd -- "$directory" && sha256sum --check --status SHA256SUMS) || die 'Accent checksum verification failed.'
}

accent_source() {
    if [[ $ACCENT != blue && ${ACCENT_OVERRIDES[$1]+yes} ]]; then printf '%s\n' "$ROOT/accents/$ACCENT/$1"
    else printf '%s\n' "$ROOT/$1"; fi
}

# Build the new copy first. Keep the previous directory only during the rename
# so an ordinary copy/promotion error or catchable signal can restore it.
replace_theme() (
    target=$1
    stage=''
    committed=false
    # ShellCheck 0.9/0.11 miss this nested function's indirect EXIT-trap call.
    # shellcheck disable=SC2317,SC2329
    cleanup() {
        result=$?
        trap - EXIT INT TERM
        if [[ -n $stage && -e $stage/previous ]] && ! $committed; then
            if ! { rm -rf -- "$target" && mv -T -- "$stage/previous" "$target"; }; then
                printf 'ERROR: Could not restore the previous theme; it is retained at %s/previous\n' "$stage" >&2
                exit 1
            fi
        fi
        [[ -z $stage ]] || rm -rf -- "$stage" || result=1
        exit "$result"
    }
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    if $DRY_RUN; then
        printf '  Prepare a complete temporary copy beside %s, then replace it.\n' "$target"
        return 0
    fi
    stage=$(mktemp -d "${target%/*}/.Adwaita-AMOLED-install.XXXXXX")
    mkdir -- "$stage/new"
    (cd -- "$ROOT" && cp -a --no-preserve=ownership --parents -- "${PAYLOAD[@]}" "$stage/new/")
    validate_runtime "$stage/new"
    if ((${#ACCENT_PAYLOAD[@]})); then
        (cd -- "$ROOT/accents/$ACCENT" && cp -a --no-preserve=ownership --parents -- "${ACCENT_PAYLOAD[@]}" "$stage/new/")
        (cd -- "$stage/new" && sha256sum --check --status "$ROOT/accents/$ACCENT/SHA256SUMS") || die 'Staged accent checksum verification failed.'
    fi
    cp --remove-destination -T -- "$stage/new/gnome-shell/gnome-shell-$SHELL_VERSION.css" "$stage/new/gnome-shell/gnome-shell.css"
    chmod -R a+rX,go-w -- "$stage/new"
    if [[ -e $target ]]; then mv -T -- "$target" "$stage/previous"; fi
    mv -T -- "$stage/new" "$target"
    committed=true
)
gtk_mode() {
    local version='' major minor
    if command -v pkg-config >/dev/null; then version=$(pkg-config --modversion gtk4 2>/dev/null) || version=''; fi
    if [[ -z $version ]] && command -v dpkg-query >/dev/null; then
        version=$(dpkg-query -W -f='${Version}' libgtk-4-1 2>/dev/null) || version=''
    fi
    if [[ -z $version ]] && command -v rpm >/dev/null; then version=$(rpm -q --qf '%{VERSION}' gtk4 2>/dev/null) || version=''; fi
    if [[ -z $version ]] && command -v pacman >/dev/null; then version=$(pacman -Q gtk4 2>/dev/null) || version=''; fi
    if [[ -z $version ]] && command -v apk >/dev/null; then version=$(apk info -v gtk4 2>/dev/null) || version=''; fi
    version=${version#*:}
    [[ $version =~ ([0-9]+)\.([0-9]+) ]] || die 'Cannot detect GTK4. Check its installed package version and use --gtk4-mode legacy or modern.'
    major=${BASH_REMATCH[1]}; minor=${BASH_REMATCH[2]}
    [[ $major == 4 ]] || die "Unexpected GTK version: $version"
    if ((10#$minor >= 16)); then printf modern; else printf legacy; fi
}
gtk_links() {
    local directory=$1 mode=$2 entry=gtk.css name
    [[ $mode == modern ]] && entry=gtk-modern.css
    for name in gtk.css gtk-dark.css libadwaita-tweaks.css assets; do
        if $REMOVE; then remove_link "$directory/$name"; else
            if [[ $name == gtk.css ]]; then
                link_file "$TARGET/extra/libadwaita/$entry" "$directory/$name"
            else link_file "$TARGET/extra/libadwaita/$name" "$directory/$name"; fi
        fi
    done
}

detected_shell=''
if command -v gnome-shell >/dev/null; then
    output=$(gnome-shell --version 2>/dev/null || :)
    [[ $output =~ ([0-9]+)\. ]] && detected_shell=${BASH_REMATCH[1]}
fi
if [[ $SHELL_VERSION == auto ]]; then
    case "$detected_shell" in 46|51) SHELL_VERSION=$detected_shell ;; *) SHELL_VERSION=51 ;; esac
fi
if $SHELL_THEME && ! $REMOVE; then
    [[ $detected_shell == 46 || $detected_shell == 51 ]] ||
        die 'Shell styling is currently verified only for GNOME 46 and 51. Install GTK without --shell on other versions.'
    [[ $SHELL_VERSION == "$detected_shell" ]] || die 'Requested Shell stylesheet does not match the installed GNOME Shell.'
fi
if $LIBADWAITA && ! $REMOVE && [[ $GTK_MODE == auto ]]; then
    if $GUIDED; then
        if GTK_MODE=$(gtk_mode 2>/dev/null); then :; else guided_gtk_mode; fi
    else GTK_MODE=$(gtk_mode); fi
fi
for extra in "${EXTRAS[@]}"; do
    case "$extra" in qt|kitty|alacritty|bat|nvim|rofi|zsh|wallpaper|all) ;; *) die "Unknown extra: $extra" ;; esac
done
for extra in "${EXTRAS[@]}"; do
    if [[ $extra == all ]]; then EXTRAS=(qt kitty alacritty bat nvim rofi zsh wallpaper); break; fi
done
for extra in "${EXTRAS[@]}"; do
    if [[ $extra == nvim && ( ${NVIM_APPNAME:-nvim} == */* || ${NVIM_APPNAME:-nvim} == . || ${NVIM_APPNAME:-nvim} == .. ) ]]; then
        die 'NVIM_APPNAME must be a single profile directory name.'
    fi
done
for app in "${FLATPAKS[@]}"; do
    [[ $app =~ ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}=(legacy|modern|gtk3)$ ]] ||
        die 'Use --flatpak APP_ID=legacy, APP_ID=modern or APP_ID=gtk3, matching the app runtime GTK version.'
    command -v flatpak >/dev/null || die 'Flatpak is not installed.'
    flatpak info "${app%=*}" >/dev/null
done
if ! $REMOVE; then
    read_runtime_files
    if [[ -f $ROOT/ARCHIVE_CONTENTS.sha256 ]]; then command -v sha256sum >/dev/null || die 'sha256sum is required to verify this archive.'; fi
    validate_runtime "$ROOT"
    if [[ $ACCENT != blue ]]; then
        command -v sha256sum >/dev/null || die 'sha256sum is required to verify accent files.'
        read_accent_files
    fi
fi

if ! $REMOVE || ((${#FLATPAKS[@]} == 0)); then
    for target in "${TARGETS[@]}"; do check_existing_theme "$target"; done
fi

# Check requested desktop tools before copying anything.
SETTINGS=()
DARK_SETTINGS=()
SCHEMA_ARGS=()
if ! $SYSTEM && ! $REMOVE; then
    if dark_targets=$(dark_preference_settings); then
        while IFS= read -r schema; do DARK_SETTINGS+=("$schema"); done <<< "$dark_targets"
    else
        printf 'App appearance unchanged: no supported writable setting. Theme installation will continue.\n'
    fi
fi
if $ACTIVATE && ! $REMOVE; then
    case ${DESKTOP^^} in
        *CINNAMON*) SETTINGS+=(org.cinnamon.desktop.interface:gtk-theme org.cinnamon.desktop.wm.preferences:theme org.cinnamon.theme:name) ;;
        *MATE*) SETTINGS+=(org.mate.interface:gtk-theme org.mate.Marco.general:theme) ;;
        *XFCE*) command -v xfconf-query >/dev/null || die 'Install xfconf or select the theme in Appearance settings.' ;;
        *GNOME*|*BUDGIE*) SETTINGS+=(org.gnome.desktop.interface:gtk-theme) ;;
        *) die 'Unknown desktop. Omit --activate and select the theme in Appearance settings.' ;;
    esac
    for setting in "${SETTINGS[@]}"; do gsettings get "${setting%:*}" "${setting#*:}" >/dev/null; done
    if $SHELL_THEME; then
        [[ ${DESKTOP^^} == *GNOME* ]] || die 'Shell activation requires a GNOME session; omit --shell on other desktops.'
        extension=user-theme@gnome-shell-extensions.gcampax.github.com
        command -v gnome-extensions >/dev/null || die 'Install and enable the GNOME User Themes extension first.'
        for schemas in "$DATA/gnome-shell/extensions/$extension/schemas" "/usr/share/gnome-shell/extensions/$extension/schemas"; do
            if [[ -f $schemas/gschemas.compiled ]]; then SCHEMA_ARGS=(--schemadir "$schemas"); break; fi
        done
        gsettings "${SCHEMA_ARGS[@]}" get org.gnome.shell.extensions.user-theme name >/dev/null
        gnome-extensions info "$extension" >/dev/null
        [[ $(gsettings get org.gnome.shell disable-user-extensions) == false ]] || die 'User extensions are disabled; enable them in Extensions before selecting a Shell theme.'
    fi
fi

if $GUIDED; then guided_review; fi

# Lock all selected theme parents before making any replacements. Removal does
# not create absent parents, and dry runs never acquire locks or create files.
if ! $DRY_RUN; then
    for target in "${TARGETS[@]}" ${GTK2_LINK:+"$GTK2_LINK"} ${LINK_PATH:+"$LINK_PATH"}; do
        parent=${target%/*}
        if ! $REMOVE; then
            # Only the selected shared parent is made public; ancestor modes stay unchanged.
            # shellcheck disable=SC2174
            if $SYSTEM; then mkdir -p -m 755 -- "$parent"; else mkdir -p -- "$parent"; fi
        fi
        lock_parent "$parent"
    done
fi
if $REMOVE; then printf 'Removing %s\n' "$THEME"; else printf 'Installing %s (%s accent)\n' "$THEME" "$ACCENT"; fi
if ! $REMOVE || ((${#FLATPAKS[@]} == 0)); then
    for target in "${TARGETS[@]}"; do
        printf 'Theme: %s\n' "$target"
        if $REMOVE; then run rm -rf -- "$target"; else replace_theme "$target"; fi
    done
fi
if [[ -n $GTK2_LINK ]]; then
    if $REMOVE; then
        [[ ! -L $GTK2_LINK ]] || run rm -f -- "$GTK2_LINK"
    elif [[ ! -L $GTK2_LINK ]]; then
        run ln -sT -- "$TARGET" "$GTK2_LINK"
    fi
fi
if [[ -n $LINK_PATH ]]; then
    if $REMOVE; then
        [[ ! -L $LINK_PATH ]] || run rm -f -- "$LINK_PATH"
    elif [[ ! -L $LINK_PATH ]]; then
        run ln -s -- "$TARGET" "$LINK_PATH"
    fi
fi
if $LIBADWAITA || { $REMOVE && ! $SYSTEM && ((${#FLATPAKS[@]} == 0)); }; then gtk_links "$CONFIG/gtk-4.0" "$GTK_MODE"; fi

extra_file() {
    if $REMOVE; then run rm -f -- "$2"; else copy_file "$(accent_source "extra/$1")" "$2"; fi
}
for extra in "${EXTRAS[@]}"; do
    case "$extra" in
        qt) for qt in qt5ct qt6ct; do
                for file in colors/Adwaita-AMOLED.conf qss/fusion-simple-scrollbar.qss; do extra_file "$qt/$file" "$CONFIG/$qt/$file"; done
            done ;;
        kitty) extra_file kitty/adwaita-amoled.conf "${KITTY_CONFIG_DIRECTORY:-$CONFIG/kitty}/themes/adwaita-amoled.conf" ;;
        alacritty) extra_file alacritty/alacritty.toml "$CONFIG/alacritty/themes/adwaita-amoled.toml" ;;
        bat) bat_dir=${BAT_CONFIG_PATH:+$(dirname -- "$BAT_CONFIG_PATH")}; bat_dir=${bat_dir:-$CONFIG/bat}
            executable=$(command -v bat || command -v batcat || :)
            if [[ -n $executable && -z ${BAT_CONFIG_PATH:-} ]]; then bat_dir=$("$executable" --config-dir); fi
            extra_file bat/themes/adwaita-amoled.tmTheme "$bat_dir/themes/adwaita-amoled.tmTheme"
            if [[ -n $executable ]]; then run "$executable" cache --build; fi ;;
        nvim) profile=${NVIM_APPNAME:-nvim}
            for file in colors/adwaita-amoled.vim autoload/airline/themes/adwaita_amoled.vim; do extra_file "nvim/$file" "$CONFIG/$profile/$file"; done ;;
        rofi) extra_file rofi/adwaita-dark.rasi "$CONFIG/rofi/themes/adwaita-amoled.rasi" ;;
        zsh) extra_file zsh/.zshrc "$CONFIG/zsh/adwaita-amoled.zsh" ;;
        wallpaper) extra_file wallpaper/blackmount.png "$DATA/backgrounds/$THEME/blackmount.png" ;;
    esac
done
for app in "${FLATPAKS[@]}"; do
    mode=${app#*=}; app=${app%=*}
    if $REMOVE; then
        gtk_links "$HOME/.var/app/$app/config/gtk-4.0" "$mode"
        run flatpak override --user --nofilesystem="$TARGET" "$app"
        if [[ $mode == gtk3 ]]; then run flatpak override --user --unset-env=GTK_THEME "$app"; fi
    else
        run flatpak override --user --filesystem="$TARGET:ro" "$app"
        if [[ $mode == gtk3 ]]; then run flatpak override --user --env=GTK_THEME="$THEME" "$app"
        else gtk_links "$HOME/.var/app/$app/config/gtk-4.0" "$mode"; fi
    fi
done
if $ACTIVATE && ! $REMOVE; then
    for setting in "${SETTINGS[@]}"; do run gsettings set "${setting%:*}" "${setting#*:}" "$THEME"; done
    if [[ ${DESKTOP^^} == *XFCE* ]]; then
        run xfconf-query -c xsettings -p /Net/ThemeName --create -t string -s "$THEME"
    fi
    if $SHELL_THEME; then
        run gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com
        run gsettings "${SCHEMA_ARGS[@]}" set org.gnome.shell.extensions.user-theme name "$THEME"
    fi
fi
for schema in "${DARK_SETTINGS[@]}"; do
    printf 'Application appearance: prefer-dark (%s color-scheme)\n' "$schema"
    if ! run gsettings set "$schema" color-scheme prefer-dark; then
        printf 'Could not set dark appearance: %s color-scheme. Select dark appearance in desktop/app settings.\n' "$schema" >&2
    fi
done
if $DRY_RUN; then printf 'Dry run: nothing changed.\n'; else printf 'Done. Restart affected applications; reload GNOME Shell themes by logging out/in.\n'; fi
if (("${#EXTRAS[@]}")) && ! $DRY_RUN; then
    if $REMOVE; then printf 'Selected app theme files removed. Existing app settings were not rewritten.\n'
    else printf 'App theme files copied. Select them in each app; see INSTALLING.md. Existing app settings were not rewritten.\n'; fi
fi
