#!/usr/bin/env bash
# Sourced only by install.sh's interactive entry point. No files/settings change here.
# Shared variables and the selected argument arrays are consumed by install.sh.
# shellcheck disable=SC2034

menu_read() {
    printf '%s ' "$1"
    if ! IFS= read -r MENU_REPLY; then
        printf '\nCancelled; no changes made.\n'
        exit 0
    fi
}

menu_number() {
    local maximum=$1 default=$2
    while true; do
        menu_read "Choose [${default}]:"
        MENU_REPLY=${MENU_REPLY:-$default}
        if [[ $MENU_REPLY =~ ^[0-9]{1,6}$ ]] && ((10#$MENU_REPLY <= maximum)); then
            MENU_NUMBER=$((10#$MENU_REPLY))
            return
        fi
        printf 'Enter a number from 0 to %s.\n' "$maximum"
    done
}

menu_yes() {
    local prompt=$1 default=${2:-n} hint='[y/N]'
    [[ $default != y ]] || hint='[Y/n]'
    while true; do
        menu_read "$prompt $hint"
        case ${MENU_REPLY,,} in
            y|yes) return 0 ;;
            n|no) return 1 ;;
            '') [[ $default == y ]]; return ;;
            *) printf 'Enter y for yes or n for no.\n' ;;
        esac
    done
}

guided_extras() {
    local i mark key
    local -a keys=(qt kitty alacritty bat nvim rofi zsh wallpaper) chosen=()
    local -a labels=('Qt palettes (select in qt5ct/qt6ct)' 'Kitty terminal theme'
        'Alacritty terminal theme' 'bat syntax theme' 'Neovim and Airline themes'
        'Rofi launcher theme' 'Zsh prompt/plugin colors' 'Wallpaper')
    local -A selected=()
    while true; do
        printf '\nOptional extras: choose a number to toggle it.\n'
        for i in "${!keys[@]}"; do
            mark=' '; [[ ! ${selected[${keys[$i]}]+yes} ]] || mark=x
            printf '  %s. [%s] %s\n' "$((i+1))" "$mark" "${labels[$i]}"
        done
        printf '  9. Select all\n  0. Done\n'
        menu_number 9 0
        case $MENU_NUMBER in
            0) break ;;
            9) for key in "${keys[@]}"; do selected[$key]=1; done ;;
            *) key=${keys[$((MENU_NUMBER-1))]}
                if [[ ${selected[$key]+yes} ]]; then unset 'selected[$key]'; else selected[$key]=1; fi ;;
        esac
    done
    for key in "${keys[@]}"; do [[ ! ${selected[$key]+yes} ]] || chosen+=("$key"); done
    if ((${#chosen[@]})); then
        local joined
        joined=$(IFS=,; printf '%s' "${chosen[*]}")
        MENU_ARGS+=(--extras "$joined")
    fi
    printf 'Extras copy theme snippets; select/include them in each app afterward.\n'
}

guided_flatpaks() {
    local listing id name index mode selected_index
    local -a ids=() names=() modes=()
    local -A listed=()
    MENU_APP_ARGS=()
    if ! command -v flatpak >/dev/null; then printf 'Flatpak is not installed.\n'; return 1; fi
    if ! listing=$(flatpak list --app --columns=application,name 2>/dev/null); then
        printf 'Could not list installed Flatpak applications; nothing selected.\n'; return 1
    fi
    while IFS=$'\t' read -r id name; do
        [[ $id =~ ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}$ ]] || continue
        [[ ! ${listed[$id]+yes} ]] || continue
        listed[$id]=1
        ids+=("$id"); names+=("${name:-$id}"); modes+=('')
    done <<< "$listing"
    if ((${#ids[@]} == 0)); then printf 'No installed Flatpak applications found.\n'; return 1; fi
    while true; do
        printf '\nSelect an installed Flatpak application:\n'
        for index in "${!ids[@]}"; do
            printf '  %s. %s (%s)' "$((index+1))" "${names[$index]}" "${ids[$index]}"
            [[ -z ${modes[$index]} ]] || printf ' [selected: %s]' "${modes[$index]}"
            printf '\n'
        done
        printf '  0. Done\n'
        menu_number "${#ids[@]}" 0
        ((MENU_NUMBER != 0)) || break
        selected_index=$((MENU_NUMBER-1))
        printf '\nMatch this app runtime, which can differ from your desktop GTK version.\n'
        printf '  1. GTK3\n  2. GTK4 older than 4.16\n  3. GTK4 4.16 or newer\n  0. Skip / clear selection if unsure\n'
        menu_number 3 0
        case $MENU_NUMBER in 1) mode=gtk3 ;; 2) mode=legacy ;; 3) mode=modern ;; 0) mode='' ;; esac
        modes[selected_index]=$mode
    done
    for index in "${!ids[@]}"; do
        [[ -z ${modes[$index]} ]] || MENU_APP_ARGS+=(--flatpak "${ids[$index]}=${modes[$index]}")
    done
    ((${#MENU_APP_ARGS[@]} != 0))
}

guided_system() {
    if ((EUID != 0)); then
        command -v sudo >/dev/null || die 'Administrator setup needs sudo. Ask your administrator to run sudo ./install.sh --interactive.'
        printf '\nOpening shared theme setup. sudo may ask for your password.\n'
        exec sudo -- bash "$ROOT/install.sh" --interactive
    fi
    printf '\nShared system theme (administrator)\n'
    printf 'Copies theme files for all users; personal GTK4/app settings stay separate.\n'
    printf '  1. Install/update\n  2. Remove\n  0. Exit\n'
    menu_number 2 0
    MENU_ARGS=(--system)
    case $MENU_NUMBER in 0) printf 'Cancelled; no changes made.\n'; exit 0 ;; 2) MENU_ARGS+=(--remove) ;; esac
    printf '\nSelect the theme location (use the original location when removing):\n'
    printf '  1. /usr/local/share/themes (recommended)\n  2. /usr/share/themes (real copy)\n  0. Exit\n'
    menu_number 2 1
    case $MENU_NUMBER in
        0) printf 'Cancelled; no changes made.\n'; exit 0 ;;
        2) MENU_ARGS+=(--dest /usr/share/themes) ;;
        1) printf 'GTK2 needs the shared theme exposed under /usr/share/themes.\n'
           if menu_yes 'Also manage a link under /usr/share/themes to this root-owned copy?' n; then
               MENU_ARGS+=(--link /usr/share/themes)
           fi ;;
    esac
}

guided_advanced() {
    while true; do
        printf '\nAdvanced options\n  1. Shared system theme (administrator)\n'
        printf '  2. Configure selected Flatpak apps\n  3. Remove styling from selected Flatpak apps\n  0. Back\n'
        menu_number 3 0
        case $MENU_NUMBER in
            0) return 1 ;;
            1) guided_system; return 0 ;;
            2) if guided_flatpaks; then MENU_ARGS=(install "${MENU_APP_ARGS[@]}"); return 0; fi ;;
            3) if guided_flatpaks; then MENU_ARGS=(--remove "${MENU_APP_ARGS[@]}"); return 0; fi ;;
        esac
    done
}

guided_user_themes_ready() {
    local extension=user-theme@gnome-shell-extensions.gcampax.github.com schemas
    local -a schema_args=()
    command -v gnome-extensions >/dev/null && command -v gsettings >/dev/null || return 1
    gnome-extensions info "$extension" >/dev/null 2>&1 || return 1
    for schemas in "$DATA/gnome-shell/extensions/$extension/schemas" "/usr/share/gnome-shell/extensions/$extension/schemas"; do
        if [[ -f $schemas/gschemas.compiled ]]; then schema_args=(--schemadir "$schemas"); break; fi
    done
    gsettings "${schema_args[@]}" get org.gnome.shell.extensions.user-theme name >/dev/null 2>&1 || return 1
    [[ $(gsettings get org.gnome.shell disable-user-extensions 2>/dev/null) == false ]]
}

guided_setup() {
    MENU_ARGS=()
    if [[ -n ${SUDO_USER:-} ]] && ((EUID == 0)); then guided_system; return; fi
    local existing=false default=y version='' output name select_desktop=false gnome_desktop=false
    while true; do
        printf '\nAdwaita-AMOLED setup\n\n  1. Install/update for this user (recommended)\n'
        printf '  2. Remove for this user\n  3. Help\n  4. Advanced options\n  0. Exit\n'
        menu_number 4 1
        case $MENU_NUMBER in
            0) printf 'Cancelled; no changes made.\n'; exit 0 ;;
            1) MENU_ARGS=(install); break ;;
            2) MENU_ARGS=(--remove); break ;;
            3) printf '\nSetup shows a review before changing anything. Choose Preview to print operations only.\nGTK4/libadwaita styles modern GNOME apps through user CSS. Existing overrides are replaced only if selected.\nExtras need selection in each app. Root/shared and selected-app Flatpak setup are under Advanced options.\nFor command-line options, run ./install.sh --help.\n' ;;
            4) if guided_advanced; then return; fi ;;
        esac
    done
    printf '\nDesktop: %s\nTheme files: %s/%s\n' "${DESKTOP:-not detected}" "$DEST" "$THEME"
    if [[ ${MENU_ARGS[0]} == --remove ]]; then
        if menu_yes "Remove this theme's native GTK4 links too? Custom replacement CSS is kept." y; then MENU_ARGS+=(-l); fi
        if menu_yes 'Also remove selected copied app themes or wallpaper?' n; then guided_extras; fi
        printf 'Flatpak styling is separate: remove it under Advanced options before deleting the shared theme files.\n'
        return
    fi
    for name in gtk.css gtk-dark.css libadwaita-tweaks.css assets; do
        [[ ! -e $CONFIG/gtk-4.0/$name && ! -L $CONFIG/gtk-4.0/$name ]] || existing=true
    done
    printf '\nGTK4/libadwaita setup replaces gtk.css, gtk-dark.css, libadwaita-tweaks.css and assets\nunder %s/gtk-4.0, without backups. Other settings are kept.\n' "$CONFIG"
    if $existing; then default=n; printf 'Existing override paths found; replacement is optional.\n'; fi
    if menu_yes 'Apply the theme to native GTK4/libadwaita apps too?' "$default"; then MENU_ARGS+=(-l); fi
    case ${DESKTOP^^} in
        *XFCE*)
            if command -v xfconf-query >/dev/null; then
                if menu_yes 'Select Adwaita-AMOLED in Xfce now?' y; then select_desktop=true; fi
            else printf 'xfconf is unavailable; select the theme in Appearance settings afterward.\n'; fi ;;
        *GNOME*|*BUDGIE*|*CINNAMON*|*MATE*)
            if command -v gsettings >/dev/null; then
                if menu_yes 'Select Adwaita-AMOLED for this desktop now?' y; then select_desktop=true; fi
            else printf 'gsettings is unavailable; select the theme in Appearance settings afterward.\n'; fi ;;
        *) printf 'Select Adwaita-AMOLED manually in your desktop Appearance settings afterward.\n' ;;
    esac
    if $select_desktop; then MENU_ARGS+=(--activate); fi
    if dark_preference_settings >/dev/null 2>&1; then
        printf '\nDark appearance is separate from GTK theme selection. This preference affects apps that honor it; explicit app themes still take precedence.\n'
        if menu_yes 'Prefer dark appearance in applications such as Firefox?' y; then MENU_ARGS+=(--prefer-dark); fi
    else
        printf 'No supported writable app appearance preference detected; use your desktop/app Appearance settings if apps stay light.\n'
    fi
    case ${DESKTOP^^} in
        *BUDGIE*|*CINNAMON*|*MATE*|*XFCE*) ;; # These sessions may also include :GNOME.
        *GNOME*) gnome_desktop=true ;;
    esac
    if $gnome_desktop && command -v gnome-shell >/dev/null; then
        output=$(gnome-shell --version 2>/dev/null || :)
        [[ ! $output =~ ([0-9]+)\. ]] || version=${BASH_REMATCH[1]}
        if [[ $version == 46 || $version == 51 ]]; then
            if $select_desktop && guided_user_themes_ready; then
                printf 'User Themes is available. GDM/login screens are separate.\n'
                if menu_yes 'Apply the matching GNOME Shell theme with User Themes too?' n; then MENU_ARGS+=(--shell); fi
            else
                printf 'The matching Shell files are included. To apply them, install/allow User Themes and select Adwaita-AMOLED there, or rerun setup with desktop selection.\n'
            fi
        else printf 'Shell styling is verified only for GNOME 46/51; continuing with GTK/app themes.\n'; fi
    fi
    if menu_yes 'Copy optional application themes or wallpaper?' n; then guided_extras; fi
    if command -v flatpak >/dev/null && menu_yes 'Configure selected Flatpak apps too?' n; then
        if guided_flatpaks; then MENU_ARGS+=("${MENU_APP_ARGS[@]}"); fi
    fi
}

guided_gtk_mode() {
    printf '\nCould not detect native GTK4. Check the GTK package version, not the GNOME version.\n'
    printf '  1. GTK4 older than 4.16\n  2. GTK4 4.16 or newer\n  0. Skip GTK4 overrides if unsure\n'
    menu_number 2 0
    case $MENU_NUMBER in 1) GTK_MODE=legacy ;; 2) GTK_MODE=modern ;; 0) LIBADWAITA=false ;; esac
}

guided_review() {
    local path extra directory executable
    printf '\nReview selected changes\n'
    if $REMOVE && ((${#FLATPAKS[@]})); then
        printf 'Remove selected Flatpak styling; installed theme files will be kept.\n'
    else
        if $REMOVE; then printf 'Remove theme files:\n'; else printf 'Install/update theme files:\n'; fi
        printf '  %s\n' "${TARGETS[@]}"
    fi
    [[ -z $LINK_PATH ]] || printf 'Shared link: %s -> %s\n' "$LINK_PATH" "$TARGET"
    [[ -z $GTK2_LINK ]] || printf 'GTK2 compatibility link: %s -> %s\n' "$GTK2_LINK" "$TARGET"
    if $LIBADWAITA; then
        if $REMOVE; then printf 'Unlink only this theme\047s GTK4 overrides in %s/gtk-4.0\n' "$CONFIG"
        else
            printf 'GTK4 overrides (%s): %s/gtk-4.0\n' "$GTK_MODE" "$CONFIG"
            printf 'Replace gtk.css, gtk-dark.css, libadwaita-tweaks.css and assets without backups.\n'
            for path in gtk.css gtk-dark.css libadwaita-tweaks.css assets; do
                [[ ! -e $CONFIG/gtk-4.0/$path && ! -L $CONFIG/gtk-4.0/$path ]] || printf '  Existing: %s/gtk-4.0/%s\n' "$CONFIG" "$path"
            done
        fi
    fi
    for extra in "${EXTRAS[@]}"; do
        case $extra in
            qt) printf 'Qt colors/QSS: %s/qt5ct and %s/qt6ct\n' "$CONFIG" "$CONFIG" ;;
            kitty) printf 'Kitty snippet: %s/themes/adwaita-amoled.conf\n' "${KITTY_CONFIG_DIRECTORY:-$CONFIG/kitty}" ;;
            alacritty) printf 'Alacritty snippet: %s/alacritty/themes/adwaita-amoled.toml\n' "$CONFIG" ;;
            bat) directory=${BAT_CONFIG_PATH:+$(dirname -- "$BAT_CONFIG_PATH")}; directory=${directory:-$CONFIG/bat}
                executable=$(command -v bat || command -v batcat || :)
                if [[ -n $executable && -z ${BAT_CONFIG_PATH:-} ]]; then directory=$("$executable" --config-dir); fi
                printf 'bat theme: %s/themes/adwaita-amoled.tmTheme (rebuild cache if installed)\n' "$directory" ;;
            nvim) printf 'Neovim colors/Airline: %s/%s\n' "$CONFIG" "${NVIM_APPNAME:-nvim}" ;;
            rofi) printf 'Rofi snippet: %s/rofi/themes/adwaita-amoled.rasi\n' "$CONFIG" ;;
            zsh) printf 'Zsh snippet: %s/zsh/adwaita-amoled.zsh\n' "$CONFIG" ;;
            wallpaper) printf 'Wallpaper: %s/backgrounds/%s/blackmount.png\n' "$DATA" "$THEME" ;;
        esac
    done
    for path in "${FLATPAKS[@]}"; do
        printf 'Flatpak %s: %s (per-app override; GTK4 modes also manage links in %s/.var/app/%s/config/gtk-4.0)\n' "${path%=*}" "${path#*=}" "$HOME" "${path%=*}"
    done
    if $SHELL_THEME; then printf 'GNOME Shell stylesheet: %s\n' "$SHELL_VERSION"; fi
    if $ACTIVATE; then printf 'Select desktop theme for: %s\n' "$DESKTOP"; fi
    if $PREFER_DARK; then
        printf 'Prefer dark appearance in supporting applications:\n'
        for path in "${DARK_SETTINGS[@]}"; do printf '  %s color-scheme = prefer-dark\n' "$path"; done
        printf 'This user preference is separate from the theme and remains selected after removal. Firefox must use System theme — auto to follow it.\n'
    fi
    if $REMOVE; then printf 'Removed files and earlier desktop preferences are not restored.\n'; fi
    if ((${#EXTRAS[@]})); then printf 'Personal app settings stay unchanged; select/include installed snippets in each app.\n'; fi
    printf '\n'
    while true; do
        menu_read 'Apply these changes? [y/N/p=preview]'
        case ${MENU_REPLY,,} in
            y|yes) return ;;
            p|preview) DRY_RUN=true; return ;;
            ''|n|no|0) printf 'Cancelled; no changes made.\n'; exit 0 ;;
            *) printf 'Enter y to apply, n to cancel or p to preview without changes.\n' ;;
        esac
    done
}
