#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  Adwaita-AMOLED — build script
#  Compiles source CSS into gtk.gresource bundles for gtk-3.0 and gtk-4.0.
#
#  EDITING THE THEME
#  ─────────────────
#  1. Edit source files in src/gtk-3.0/ or src/gtk-4.0/
#  2. Run:  ./build.sh
#  3. Run:  ./build.sh --install   (also copies to ~/.local/share/themes/)
#
#  SOURCE FILES
#  ─────────────────
#  src/gtk-3.0/gtk-main.css      — main GTK3 stylesheet (xfce4 panel included)
#  src/gtk-4.0/gtk-main.css      — GTK4 color overrides + libadwaita tweaks
#  src/gtk-4.0/assets/*.svg      — checkbox/radio SVG assets
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

THEME_NAME="Adwaita-AMOLED"
THEME_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC3="$THEME_DIR/src/gtk-3.0"
SRC4="$THEME_DIR/src/gtk-4.0"
OUT3="$THEME_DIR/gtk-3.0"
OUT4="$THEME_DIR/gtk-4.0"
INSTALL_DIR="$HOME/.local/share/themes/$THEME_NAME"

# ── Dependency check ──────────────────────────────────────────────────────────
if ! command -v glib-compile-resources &>/dev/null; then
    echo "ERROR: glib-compile-resources not found."
    echo "Install with:  sudo pacman -S glib2        (Arch/Artix)"
    echo "           or: sudo apt install libglib2.0-dev  (Debian/Ubuntu)"
    exit 1
fi

# ── GTK3 ──────────────────────────────────────────────────────────────────────
echo "Building gtk-3.0..."
glib-compile-resources \
    "$SRC3/adwaita-amoled-gtk3.gresource.xml" \
    --target="$OUT3/gtk.gresource" \
    --sourcedir="$SRC3"
echo "  → gtk-3.0/gtk.gresource ($(du -sh "$OUT3/gtk.gresource" | cut -f1))"

# ── GTK4 ──────────────────────────────────────────────────────────────────────
echo "Building gtk-4.0..."
glib-compile-resources \
    "$SRC4/adwaita-amoled-gtk4.gresource.xml" \
    --target="$OUT4/gtk.gresource" \
    --sourcedir="$SRC4"
echo "  → gtk-4.0/gtk.gresource ($(du -sh "$OUT4/gtk.gresource" | cut -f1))"

echo "Build complete."

# ── Optional install ──────────────────────────────────────────────────────────
if [[ "${1:-}" == "--install" ]]; then
    echo ""
    echo "Installing to $INSTALL_DIR ..."
    mkdir -p "$INSTALL_DIR"
    # Copy everything except the src/ directory (that stays in your repo)
    rsync -a --exclude='src/' --exclude='.git/' "$THEME_DIR/" "$INSTALL_DIR/"

    # ~/.config/gtk-4.0/ — libadwaita user override path
    # NOTE: GTK4 only reads gtk.css here; it does NOT scan for or register
    # a gtk.gresource in this directory.  resource:// URIs would silently
    # fail.  We copy the real source CSS directly — it is only ~185 lines
    # so there is no performance reason to bundle it.
    mkdir -p "$HOME/.config/gtk-4.0"
    cp "$SRC4/gtk-main.css" "$HOME/.config/gtk-4.0/gtk.css"
    echo "  → $INSTALL_DIR"
    echo "  → ~/.config/gtk-4.0/gtk.css (source CSS, not a resource redirect)"
    echo "Done. Restart your apps to see changes."
fi
