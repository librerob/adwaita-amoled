# GNOME Shell 51 AMOLED theme

This is GNOME Shell **51.1**'s default dark theme with an AMOLED palette. It
targets **GNOME Shell 51.x**; other major Shell versions have not been verified.
The compiled `gnome-shell.css` and matching local SVG assets are included.

The adaptation keeps upstream layout, widget states, privacy indicators and
GNOME's selected system accent hue. Opaque accent fills are darkened by state
to preserve white-label contrast; standalone system accents remain lighter. Panel, menu, dialog and overview bases
are black; raised surfaces and OSDs use the existing AMOLED depth palette.
The desktop wallpaper remains your choice.

## Install and activate

Install or update the complete theme directory as described in the main
[README](../README.md#installation), retaining this folder and its assets.
Install GNOME's [User Themes extension](https://extensions.gnome.org/extension/19/user-themes/)
and enable it:

```bash
gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com
gnome-extensions prefs user-theme@gnome-shell-extensions.gcampax.github.com
```

Choose **Adwaita-AMOLED** in the extension's settings. If you installed the
extension during the current session, log out and back in first so Shell can
detect it. Selecting a GTK theme alone does not select the Shell theme.

After updating this directory, toggle User Themes off and on to reload the
stylesheet. Keep `assets/` beside `gnome-shell.css`. This themes your logged-in
Shell session; it does not replace GDM's system login-screen resources.

## Source and rebuilding

Upstream: [GNOME Shell 51.1 theme](https://github.com/GNOME/gnome-shell/tree/51.1/data/theme),
commit `33da06854e229c256afd5872fedd83c28cbfa176`.
`UPSTREAM.json` records the original paths and SHA-256 of the unmodified Sass
sources and SVG assets. Upstream files remain unchanged under `sass/upstream/`.
The palette adaptation is in `sass/_amoled.scss`, loaded before upstream drawing
and widget rules by `sass/gnome-shell.scss`. Color-only overrides in
`sass/_readability.scss` handle accent-filled control states without editing
the pinned upstream sources. See [color readability coverage](../COLOR_READABILITY.md).

Rebuild after editing the palette:

```bash
sudo apt install sassc
./gnome-shell/build.sh
```

Run the build command from the repository/theme root. The script also accepts an
output filename as its first argument for reproducibility checks. It rewrites
upstream resource URLs to the bundled assets. GTK resource bundles are built
separately by the root `build.sh`.

GNOME Shell Sass is GPL-2.0-or-later; its license and attribution are retained in
`sass/upstream/COPYING`, `sass/upstream/README.md` and the source files. The
LGPL-2.1 notice in the upstream common stylesheet is retained, and the license
text is included as `COPYING.LGPL`. AMOLED modifications are marked and dated
2026-10-16. See the root [compatibility report](../COMPATIBILITY.md) for actual
validation and remaining limits.
