# GNOME Shell 46 and 51 AMOLED themes

These are GNOME Shell **46.10** and **51.1**'s default dark themes with an AMOLED
palette. They target **46.x and 51.x** respectively; other major Shell versions
have not been verified. Each variant retains its own upstream widget structures.
GNOME 46 uses SVG switches and different quick-settings classes; loading the
51 stylesheet on 46 causes missing interaction backgrounds and switch handles.

The adaptation keeps upstream layout, widget states and privacy indicators.
GNOME 46 matches the selected theme accent. The default blue installation on
GNOME 51 retains its selected system accent hue. The seven optional named
presets instead use their selected theme color on GNOME 51 too; changing GNOME
Settings' accent does not recolor those Shell presets. Select a preset through
the installer's Accent color menu or `--accent purple`.
Opaque accent fills are darkened by state
to preserve white-label contrast; standalone system accents remain lighter. Panel, menu, dialog and overview bases
are black; raised surfaces and OSDs use the existing AMOLED depth palette.
The desktop wallpaper remains your choice.

## Install and activate

Install or update the complete theme directory as described in the main
[README](../README.md#installation), retaining this folder and its assets.
Install GNOME's [User Themes extension](https://extensions.gnome.org/extension/19/user-themes/)
and log in again if it was just installed. The installer can enable/select it:

```bash
./install.sh -l --shell --activate --dry-run
./install.sh -l --shell --activate
```

Alternatively, enable and select it manually:

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

The installer automatically selects the locally installed GNOME 46 or 51 variant,
including on updates. For an explicit target, use `--shell-version 46` or `51`;
activation also checks that it matches the local Shell version.

For manual installation, copy `gnome-shell-46.css` or `gnome-shell-51.css` over
`gnome-shell.css` in the **installed** theme directory. Keep the entire `assets/`
tree, including `assets/46`. The source default remains 51; manual GNOME 46 users
must select the 46 stylesheet before enabling User Themes.

## Source and rebuilding

Upstream: [GNOME Shell 51.1 theme](https://github.com/GNOME/gnome-shell/tree/51.1/data/theme),
commit `33da06854e229c256afd5872fedd83c28cbfa176`.
`UPSTREAM.json` records the original paths and SHA-256 of the unmodified Sass
sources and SVG assets. Upstream files remain unchanged under `sass/upstream/`.
The palette adaptation is in `sass/_amoled.scss`, loaded before upstream drawing
and widget rules by `sass/gnome-shell.scss`. Color-only overrides in
`sass/_readability.scss` handle accent-filled control states without editing
the pinned upstream sources. See [color readability coverage](../COLOR_READABILITY.md).

The 46 variant is pinned to [GNOME Shell 46.10](https://github.com/GNOME/gnome-shell/tree/46.10/data/theme),
commit `49fa85b2fead489d5c1ce50ecaf28a114c831f1e`. `UPSTREAM-46.json` records all
52 upstream files/assets. Sources remain unchanged under `sass/46/upstream/`;
the entry is `sass/gnome-shell-46.scss`, with color-only overrides in
`sass/_readability-46.scss`.

Rebuild after editing the palette:

```bash
sudo apt install sassc
./gnome-shell/build.sh
./gnome-shell/build.sh --shell-version 46
```

Run the build command from the repository/theme root. The script also accepts an
output filename (after optional `--shell-version 46`) for reproducibility checks. It rewrites
upstream resource URLs to the bundled assets. GTK resource bundles are built
separately by the root `build.sh`.

The default build updates both the source default `gnome-shell.css` and its
canonical `gnome-shell-51.css`; the 46 build updates `gnome-shell-46.css`. Keeping
canonical copies allows an installed theme's updater to switch versions after a
desktop upgrade without requiring Sass at installation time.

After rebuilding the base GTK and both Shell styles, run
`python3 tools/build_accents.py` from the repository root to update all seven
precompiled overlays. Its Shell 51 adaptation resolves accent expressions by
their text/fill roles in the compiled preset CSS; selectors and layout remain
unchanged. It does not rewrite pinned upstream Sass or default blue CSS.

GNOME Shell Sass is GPL-2.0-or-later; its license and attribution are retained in
`sass/upstream/COPYING`, `sass/upstream/README.md` and the source files. The
LGPL-2.1 notice in the upstream common stylesheet is retained, and the license
text is included as `COPYING.LGPL`. AMOLED modifications are marked and dated
2026-10-16. See the root [compatibility report](../COMPATIBILITY.md) for actual
validation and remaining limits.
