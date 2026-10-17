#!/usr/bin/env bash
# Install the compiled theme directly. No Python, saved state or backup database.
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
THEME=Adwaita-AMOLED
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
CONFIG=${XDG_CONFIG_HOME:-$HOME/.config}
DESKTOP=${XDG_CURRENT_DESKTOP:-}
DEST=$DATA/themes
LIBADWAITA=false ACTIVATE=false SHELL_THEME=false SYSTEM=false REMOVE=false DRY_RUN=false
CUSTOM_DEST=false GTK_MODE=auto SHELL_VERSION=auto
EXTRAS=() FLATPAKS=() TARGETS=()
RUNTIME=(cinnamon gnome-shell gtk-2.0 gtk-3.0 gtk-4.0 metacity-1 openbox-3 extra)
DOCUMENTS=(index.theme LICENSE README.md INSTALLING.md COMPATIBILITY.md COLOR_READABILITY.md COLOR_COMPLETENESS.md install.sh)

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Install the included theme. Rerun to overwrite/update it; no backups or state.
Default destination: ${XDG_DATA_HOME:-$HOME/.local/share}/themes/Adwaita-AMOLED

  -l, --libadwaita          Replace native GTK4 override files with theme links
  -a, --activate            Select the theme for the current desktop
      --shell               Require a matching GNOME Shell theme (46 or 51)
      --extras LIST         Copy optional themes: qt,kitty,alacritty,bat,nvim,
                            rofi,zsh,wallpaper or all (select them in each app)
      --flatpak ID=MODE     Configure one app; MODE is legacy, modern or gtk3
      --gtk4-mode MODE      Native GTK4: auto, legacy (<4.16), modern (4.16+)
      --shell-version VER   auto, 46 or 51
  -d, --dest DIR            Theme parent directory
      --system              Install for all users in /usr/local/share/themes
  -r, --remove              Remove the theme and explicitly selected links/extras
      --dry-run             Print operations without changing files/settings
  -h, --help                Show this help

Examples:
  ./install.sh
  ./install.sh -l --activate
  ./install.sh --extras qt,kitty
  sudo ./install.sh --system

GTK4 linking replaces gtk.css, gtk-dark.css, libadwaita-tweaks.css and assets
under the selected gtk-4.0 config directory. No backup is created.
App themes are copied without rewriting your .zshrc, init.lua or other settings.
EOF
}

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
        --shell) SHELL_THEME=true ;;
        --system) SYSTEM=true ;;
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

[[ $GTK_MODE =~ ^(auto|legacy|modern)$ ]] || die 'GTK4 mode must be auto, legacy or modern.'
[[ $SHELL_VERSION =~ ^(auto|46|51)$ ]] || die 'Shell version must be auto, 46 or 51.'
if $SYSTEM; then
    ((EUID == 0)) || die 'Use sudo with --system.'
    $CUSTOM_DEST || DEST=/usr/local/share/themes
    if $LIBADWAITA || $ACTIVATE || (("${#EXTRAS[@]}" || "${#FLATPAKS[@]}")); then
        die '--system copies only the shared theme. Run user configuration separately without sudo.'
    fi
elif [[ -n ${SUDO_USER:-} ]]; then
    die 'Run user setup without sudo, or use --system for shared theme files.'
fi
for path in "$HOME" "$DATA" "$CONFIG" "$DEST"; do
    [[ $path == /* && $path != / && $path != *$'\n'* ]] || die "Expected an absolute directory other than /: $path"
done
DEST=$(realpath -m -- "$DEST")
TARGET=$DEST/$THEME
TARGETS+=("$TARGET")
# Refresh a legacy user copy too, so it cannot shadow the updated XDG copy.
if ! $SYSTEM && ! $CUSTOM_DEST && [[ -d $HOME/.themes/$THEME && ! -L $HOME/.themes/$THEME ]]; then
    legacy=$(realpath -m -- "$HOME/.themes/$THEME")
    [[ $legacy == "$TARGET" ]] || TARGETS+=("$legacy")
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
gtk_mode() {
    local version='' major minor
    if command -v pkg-config >/dev/null; then version=$(pkg-config --modversion gtk4 2>/dev/null || :); fi
    if [[ -z $version ]] && command -v dpkg-query >/dev/null; then
        version=$(dpkg-query -W -f='${Version}' libgtk-4-1 2>/dev/null || :)
    fi
    if [[ -z $version ]] && command -v rpm >/dev/null; then version=$(rpm -q --qf '%{VERSION}' gtk4 2>/dev/null || :); fi
    if [[ -z $version ]] && command -v pacman >/dev/null; then version=$(pacman -Q gtk4 2>/dev/null || :); fi
    if [[ -z $version ]] && command -v apk >/dev/null; then version=$(apk info -v gtk4 2>/dev/null || :); fi
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
if $LIBADWAITA && ! $REMOVE && [[ $GTK_MODE == auto ]]; then GTK_MODE=$(gtk_mode); fi
for extra in "${EXTRAS[@]}"; do
    case "$extra" in qt|kitty|alacritty|bat|nvim|rofi|zsh|wallpaper|all) ;; *) die "Unknown extra: $extra" ;; esac
done
for extra in "${EXTRAS[@]}"; do
    if [[ $extra == all ]]; then EXTRAS=(qt kitty alacritty bat nvim rofi zsh wallpaper); break; fi
done
if [[ ${NVIM_APPNAME:-nvim} == */* || ${NVIM_APPNAME:-nvim} == . || ${NVIM_APPNAME:-nvim} == .. ]]; then
    die 'NVIM_APPNAME must be a single profile directory name.'
fi
for app in "${FLATPAKS[@]}"; do
    [[ $app =~ ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}=(legacy|modern|gtk3)$ ]] ||
        die 'Use --flatpak APP_ID=legacy, APP_ID=modern or APP_ID=gtk3, matching the app runtime GTK version.'
    command -v flatpak >/dev/null || die 'Flatpak is not installed.'
    flatpak info "${app%=*}" >/dev/null
done
if ! $REMOVE; then
    for name in "${RUNTIME[@]}" "${DOCUMENTS[@]}"; do
        [[ -e $ROOT/$name ]] || die "Incomplete theme download: $name is missing."
    done
fi

# Check requested desktop tools before copying anything.
SETTINGS=()
SCHEMA_ARGS=()
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

if $REMOVE; then printf 'Removing %s\n' "$THEME"; else printf 'Installing %s\n' "$THEME"; fi
if $SYSTEM && ! $REMOVE; then run mkdir -p -m 755 -- "$DEST"; fi
if ! $REMOVE || ((${#FLATPAKS[@]} == 0)); then
    for target in "${TARGETS[@]}"; do
        printf 'Theme: %s\n' "$target"
        run rm -rf -- "$target"
        if ! $REMOVE; then
            run mkdir -p -- "$target"
            for name in "${RUNTIME[@]}" "${DOCUMENTS[@]}"; do run cp -a --no-preserve=ownership -- "$ROOT/$name" "$target/"; done
            copy_file "$ROOT/gnome-shell/gnome-shell-$SHELL_VERSION.css" "$target/gnome-shell/gnome-shell.css"
            run chmod -R a+rX,go-w -- "$target"
        fi
    done
fi
if $LIBADWAITA; then gtk_links "$CONFIG/gtk-4.0" "$GTK_MODE"; fi

extra_file() {
    if $REMOVE; then run rm -f -- "$2"; else copy_file "$ROOT/extra/$1" "$2"; fi
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
if $DRY_RUN; then printf 'Dry run: nothing changed.\n'; else printf 'Done. Restart affected applications; reload GNOME Shell themes by logging out/in.\n'; fi
if (("${#EXTRAS[@]}")); then printf 'App theme files copied. Select them in each app; see INSTALLING.md. Existing app settings were not rewritten.\n'; fi
