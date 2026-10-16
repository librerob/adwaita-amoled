#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export THEME_TEST_ROOT="$ROOT"
export LIBGL_ALWAYS_SOFTWARE=1 GDK_BACKEND=wayland GSK_RENDERER=cairo
export XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=GNOME
export WAYLAND_DISPLAY=amoled-gnome-test GSETTINGS_BACKEND=keyfile
unset DISPLAY
mkdir -p "$XDG_DATA_HOME/themes"
ln -s "$ROOT" "$XDG_DATA_HOME/themes/Adwaita-AMOLED"
gsettings set org.gnome.shell enabled-extensions "['user-theme@gnome-shell-extensions.gcampax.github.com']"
gsettings set org.gnome.shell disable-user-extensions false
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
gsettings set org.gnome.desktop.interface enable-animations true
# Avoid distribution wallpaper decoders and slideshow timing in this fixture.
gsettings set org.gnome.desktop.background picture-uri "''"
gsettings set org.gnome.desktop.background picture-uri-dark "''"
gsettings set org.gnome.desktop.background picture-options none
gsettings set org.gnome.desktop.background primary-color '#204060'
gsettings set org.gnome.shell.extensions.user-theme name Adwaita-AMOLED
exec "${GNOME_SHELL_BINARY:-gnome-shell}" --wayland --headless --no-x11 \
    --virtual-monitor 1600x1200 --wayland-display "$WAYLAND_DISPLAY" \
    --automation-script "$ROOT/tests/gnome-shell/ui.js"
