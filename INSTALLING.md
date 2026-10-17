# Installing Adwaita-AMOLED

The installer uses the included, already compiled theme. It requires Linux,
Bash and **Python 3.11 or newer**. Run the default user setup as your normal desktop user, without
`sudo`. The explicit system-wide scope below uses administrative privileges. No compiler, rsync, network access or Python package installation is
needed. GTK2 applications additionally need your distribution's **Murrine**
engine (`gtk2-engines-murrine` on Debian/Ubuntu).

## Start here

Extract an installer-enabled release, or clone the repository into a working
directory outside your installed theme directories:

```bash
git clone https://github.com/librerob/adwaita-amoled.git
cd adwaita-amoled
./install.sh
```

The terminal wizard lists components, asks which ones to configure, asks whether
to select the theme for the current desktop, and displays every destination and
preference before applying anything. Pressing Enter at the components question
selects `gtk,libadwaita` on a first installation. Type a comma-separated list to
choose extras. `all` selects every component; bat must then be installed, and
Shell activation requires GNOME Shell 51 and User Themes.

If you followed the former instructions and have
`~/.themes/Adwaita-AMOLED`, move that directory somewhere outside `~/.themes`
first, keeping it as a backup. Different consumers search the legacy directory
and the XDG directory in different orders. Setup stops on this duplicate rather
than leaving different versions active. A symlink from that legacy path to the
new installation is accepted. Existing files already at the new destination
are backed up before replacement.

Installer-enabled runtime archives include `ARCHIVE_CONTENTS.sha256`; run
`sha256sum -c ARCHIVE_CONTENTS.sha256` from the extracted theme directory to
check the included files. Older published releases without `install.sh` need
a newer installer-enabled release or this branch/checkout.

A noninteractive example, with a separate preview step:

```bash
./install.sh install --components gtk,libadwaita,kitty,nvim --activate --dry-run
./install.sh install --components gtk,libadwaita,kitty,nvim --activate --yes
```

Omit `--activate` to select the desktop theme yourself later. It only controls
desktop selection: choosing an app component such as Kitty still adds that
app's configuration. Restart affected applications after installing/updating.

## Every component and destination

In the table, `DATA` means `$XDG_DATA_HOME` (default `~/.local/share`),
`CONFIG` means `$XDG_CONFIG_HOME` (default `~/.config`), and `THEME` means
`DATA/themes/Adwaita-AMOLED`. The complete runtime theme, extras, documentation
and installer are always installed under `THEME`. Component choices control
additional configuration and desktop selection, rather than trimming that
shared directory. Source GTK files, tests and Git metadata are not copied.

| Choice | Files and behavior | What still needs your choice or an external package |
|---|---|---|
| `gtk` | Makes GTK2/3/4, Cinnamon, Metacity/Muffin/Marco and Openbox theme files available under `THEME`; with `--activate`, changes supported desktop preferences below. | Murrine for GTK2. Choose Openbox's theme through its settings. Xfwm4 decorations are not included. |
| `libadwaita` | Adds one marked `@import` to `CONFIG/gtk-4.0/gtk.css`, referencing the installed theme by an escaped absolute file URI. | This is an explicit native GTK4 user CSS override, affecting plain GTK4 and libadwaita apps. Apps may supply their own styling. |
| `qt` | Copies palettes to `CONFIG/qt5ct/colors/Adwaita-AMOLED.conf` and `CONFIG/qt6ct/colors/Adwaita-AMOLED.conf`, and the corresponding `qss/fusion-simple-scrollbar.qss` files. | Select the palette in qt5ct/qt6ct. Enable QSS separately if wanted. Install the matching Qt platform plugin; KDE may use its own integration instead. |
| `kitty` | Adds a marked include to the existing Kitty user config (`CONFIG/kitty/kitty.conf` by default), referencing `THEME/extra/kitty/adwaita-amoled.conf`. Keeps other configuration. | Honors `KITTY_CONFIG_DIRECTORY` and the standard home fallback. The snippet includes colors, cursor, tab behavior and `dim_opacity`, not just the background. |
| `alacritty` | Adds the installed TOML theme to `[general].import` in the existing Alacritty user TOML (default `CONFIG/alacritty/alacritty.toml`), preserving earlier imports and other settings. Standard `CONFIG/alacritty.toml`, `~/.config/alacritty/alacritty.toml` and `~/.alacritty.toml` fallback locations are respected. | Current TOML format, tested with 0.15.1. Local `[colors]` values override imported values. Legacy YAML, old top-level imports and ambiguous inline/dotted tables need manual migration first. A shared XDG config requires an explicit user config/manual import; shared files are not edited. |
| `bat` | Copies the syntax theme into bat's own `--config-dir` under `themes/`, adds `--theme="adwaita-amoled"` to its config, builds a cache in a temporary directory, then backs up/installs the generated cache in bat's `--cache-dir`. | Requires `bat` or `batcat`. Honors `BAT_CONFIG_PATH` and bat's reported cache directory, including `BAT_CACHE_PATH`. |
| `nvim` | Copies the colorscheme and Airline theme to `CONFIG/nvim/colors/` and `CONFIG/nvim/autoload/airline/themes/`; adds colorscheme, true-color and Airline selection to existing `init.lua` or `init.vim` (new config uses Lua). | Neovim 0.9+, true-color terminal. Airline itself is optional and not installed. Plugin managers can override a later colorscheme. Honors `NVIM_APPNAME`; refuses conflicting dual init files. |
| `rofi` | Adds a marked absolute theme import to `CONFIG/rofi/config.rasi`. | An explicit command-line theme can override it. |
| `zsh` | Adds a marked `source` to `$ZDOTDIR/.zshrc`, or `~/.zshrc` when `ZDOTDIR` is unset. | Changes prompt, completion colors, terminal title hook and optional highlighting/autosuggestion colors. Load optional plugins before the managed block. Does not install plugins or change your login shell. |
| `wallpaper` | Copies the supplied picture to `DATA/backgrounds/Adwaita-AMOLED/blackmount.png`. | Select it in background settings. The installer does not change wallpaper preferences. |
| `shell` | The Shell files are already in `THEME/gnome-shell`; with `--activate`, enables User Themes and selects Adwaita-AMOLED. | GNOME Shell **51.x**, installed/detected [User Themes](https://extensions.gnome.org/extension/19/user-themes/), and globally enabled user extensions. Log in again after installing the extension. |

### Desktop activation

`--activate` changes these preferences only when `gtk` is selected:

| Detected desktop (`XDG_CURRENT_DESKTOP`) | Preferences selected |
|---|---|
| GNOME / Budgie | `org.gnome.desktop.interface gtk-theme` |
| Cinnamon | `org.cinnamon.desktop.interface gtk-theme`, `org.cinnamon.desktop.wm.preferences theme`, `org.cinnamon.theme name` |
| MATE | `org.mate.interface gtk-theme`, `org.mate.Marco.general theme` |
| Xfce | xfconf channel `xsettings`, property `/Net/ThemeName`; existing Xfwm4 decorations stay selected |

All receive `Adwaita-AMOLED`. Unknown desktops or unavailable schemas/properties
cause an explicit activation request to stop during planning. Installation
without activation remains available. This does not select icons, cursors,
fonts, a wallpaper or a system-wide light/dark preference.

For GNOME Shell, explicitly choose `shell` as well:

```bash
./install.sh install --components gtk,libadwaita,shell --activate --dry-run
./install.sh install --components gtk,libadwaita,shell --activate --yes
```

Setup checks the running Shell major version and installed extension, enables
User Themes without changing unrelated extension membership, and sets its
`name` preference. It finds user-local extension schemas as well as system
schemas. Globally disabled extensions require your deliberate choice in the
Extensions app first. Toggle User Themes or log in again to reload an already
selected stylesheet after an update. This does not theme GDM.

### GTK4 and libadwaita: why one import

The native GTK library's version functions select `gtk-modern.css` on GTK
**4.16+**, or `gtk.css` on older GTK4. No display connection or PyGObject package
is needed for detection. If GTK4 cannot be detected, omit `libadwaita` or choose
`--gtk4-mode legacy` / `--gtk4-mode modern` explicitly after checking your native
GTK version. Rerun `update` after a system GTK upgrade; the default `auto` mode
checks again. An explicitly forced mode remains selected until changed.

The imported file loads its sibling styles/assets from the installed theme.
Updates therefore require updating that theme directory, without manually
recopying four overrides and their assets. GTK only reads the user stylesheet
when applications start; restart them to pick up changes.

Unrelated existing user CSS remains after the import and can override the
palette. An exact, known historical full-theme copy in `gtk.css` is backed up
and migrated to the import, avoiding stale definitions taking precedence.
Modified or unrecognized CSS is preserved. Old `gtk-dark.css`, assets and tweaks
beside it are left alone; the new import uses the copies inside `THEME`.

This is still an application CSS override, not an official libadwaita theme API.
The installer does not set `GTK_THEME` globally. Future toolkit/application
changes can require new compatibility work.

### Qt selection

Install qt5ct and/or qt6ct and the appropriate integration plugin through your
distribution. Open the matching configuration app, select a custom palette and
choose **Adwaita-AMOLED**. Optionally enable the installed scrollbar QSS.
Where the desktop does not provide Qt integration, launch each app with the
matching value:

```bash
QT_QPA_PLATFORMTHEME=qt5ct your-qt5-application
QT_QPA_PLATFORMTHEME=qt6ct your-qt6-application
```

One global value cannot select both plugins. Setup leaves your Qt configuration
and environment selection intact, so it also works alongside KDE's integration.

## Update, inspect and undo

After obtaining a newer checkout/release, run from that directory:

```bash
./install.sh update --dry-run
./install.sh update --yes
./install.sh status
./install.sh doctor
./install.sh uninstall --dry-run
./install.sh uninstall --yes
```

`update` reuses your saved component, GTK4 mode and desktop activation choices.
It can add components with `--components`; previous choices are retained. To
remove components, uninstall and reinstall with the desired list. The command
uses the files you downloaded; it does not fetch GitHub or silently update itself.
The installed copy at `DATA/themes/Adwaita-AMOLED/install.sh` can inspect/undo or
reapply configuration; obtaining a newer source/package is necessary to update
its theme files.

`status` and `doctor` currently provide the same read-only integrity report:
native GTK version, detected desktop, selected components and Flatpak apps, missing/edited paths,
changed managed desktop preferences, state and backup locations. They return a
nonzero status for detected differences or an interrupted transaction. They do
not render your applications or diagnose hardware.

### Backups and preservation

State lives in `$XDG_STATE_HOME/adwaita-amoled` (default
`~/.local/state/adwaita-amoled`). `state.json` records original bytes, file modes,
symlinks, managed fragments and desktop preference values. Each applied
transaction retains a dated JSON record under `backups/`; its before-images
contain file bytes encoded as base64, not a separate theme-only tarball. Records
are private files (mode 600, newly created state directories mode 700), since
app configurations can contain private information. Keep this directory to
retain undo history. Backups are not removed automatically.

Planning checks all selected configurations before changing theme files. A
lock prevents simultaneous installers. Atomic file replacement and a journal
allow rollback on failures and recovery on the next install/update/uninstall
after an interruption. A dry run creates no files. A cancelled/failed normal
preflight may leave only an empty state directory and lock.

Undo restores pre-install files and modes, restores replaced leaf symlinks,
removes newly installed files and restores unchanged managed desktop values.
User edits outside marked blocks are retained, including edits made before an
update. Desktop choices changed later are kept. Extension-list undo removes or
restores only this installer's membership changes, preserving other extensions.
Later rebuilt bat caches are kept if changed. Empty directories, state and backup
records remain. Uninstall does not remove dependencies or old manual copies.

Edits to an installed theme file, or to the inside of a managed block, stop
update/undo with the conflicting path. Save your edit elsewhere and resolve the
conflict before retrying. Setup does not overwrite it blindly. Leaf config
symlinks are replaced by backed-up regular files without editing their target;
undo restores the link. Nested symlinked configuration directories are refused;
use their real XDG root or configure that component manually.

## Manual installation

The compiled theme can also be installed manually. These commands do not require
Python or a compiler. Run them from the extracted theme/repository directory as
your normal user. GTK2 still needs Murrine.

### Theme files and desktop selection

Keep a backup of an existing installed theme before replacing its files. Avoid
keeping a second copy named Adwaita-AMOLED in `~/.themes`, because different
desktop components search the legacy and XDG locations in different orders.

```bash
amoled_data="${XDG_DATA_HOME:-$HOME/.local/share}"
amoled_theme="$amoled_data/themes/Adwaita-AMOLED"
mkdir -p "$amoled_theme"
cp -R cinnamon gnome-shell gtk-2.0 gtk-3.0 gtk-4.0 metacity-1 openbox-3 extra "$amoled_theme/"
cp index.theme LICENSE "$amoled_theme/"
```

Select **Adwaita-AMOLED** in your desktop's Appearance settings. For GNOME/Budgie,
the GTK setting can also be selected with:

```bash
gsettings set org.gnome.desktop.interface gtk-theme Adwaita-AMOLED
```

Cinnamon, MATE and Xfce use their own preferences listed in
[Desktop activation](#desktop-activation). Select Openbox's theme through its
settings. GNOME Shell requires User Themes and a separate Shell theme selection;
see [the Shell guide](gnome-shell/README.md). No Xfwm4 decoration theme is included.

### GTK4 and libadwaita overrides

Manual copying replaces the active GTK4 override files. Back up the existing
directory first; custom CSS can be merged back afterward. Use **`gtk-modern.css`
for GTK 4.16+**, or **`gtk.css` for older GTK4**. Check the GTK4 package version
installed by your distribution; the relevant version is GTK, not GNOME's version.
The installer performs this choice automatically if you prefer not to manage it.

```bash
amoled_theme="${XDG_DATA_HOME:-$HOME/.local/share}/themes/Adwaita-AMOLED"
amoled_gtk4="${XDG_CONFIG_HOME:-$HOME/.config}/gtk-4.0"
if [ -e "$amoled_gtk4" ]; then
  amoled_gtk4_backup=$(mktemp -d "$amoled_gtk4.backup.XXXXXX")
  cp -a "$amoled_gtk4/." "$amoled_gtk4_backup/"
fi
mkdir -p "$amoled_gtk4/assets"
cp "$amoled_theme/extra/libadwaita/gtk-dark.css" "$amoled_gtk4/"
cp "$amoled_theme/extra/libadwaita/libadwaita-tweaks.css" "$amoled_gtk4/"
cp -R "$amoled_theme/extra/libadwaita/assets/." "$amoled_gtk4/assets/"
```

Then run **one** of these, according to your GTK version:

```bash
# GTK 4.16 or newer:
cp "$amoled_theme/extra/libadwaita/gtk-modern.css" "$amoled_gtk4/gtk.css"
```

```bash
# Older GTK4:
cp "$amoled_theme/extra/libadwaita/gtk.css" "$amoled_gtk4/gtk.css"
```

Restart applications. Repeat these copies when updating the theme. To undo a
manual override, restore the directory backup you made. The installer's undo
only manages files it recorded; it cannot undo untracked manual changes.
Do not combine manual replacement with a tracked installer-managed file; undo
the managed setup first or use `update` to keep its history consistent.

### Manual extras

These examples use the same `amoled_theme` variable above and default XDG paths;
adjust application-specific locations if you use a custom profile or config.
Merge the indicated line into the existing configuration rather than replacing
that configuration wholesale.

| Extra | Manual installation/selection |
|---|---|
| Kitty | Add `include /absolute/path/to/Adwaita-AMOLED/extra/kitty/adwaita-amoled.conf` to the active `kitty.conf`. The snippet changes cursor/tab settings and dimming as well as colors. |
| Alacritty | Merge `import = ["/absolute/path/to/Adwaita-AMOLED/extra/alacritty/alacritty.toml"]` into `[general]` in the active TOML file. Preserve existing imports. Local colors take precedence. |
| bat | Copy `extra/bat/themes/adwaita-amoled.tmTheme` into the `themes/` subdirectory reported by `bat --config-dir`; add `--theme="adwaita-amoled"` to its config, then run `bat cache --build` (or `batcat`). |
| Neovim | Copy `extra/nvim/colors/adwaita-amoled.vim` into your profile's `colors/` directory. Enable true color and select the colorscheme as shown below. |
| Airline | Copy `extra/nvim/autoload/airline/themes/adwaita_amoled.vim` into the corresponding Neovim `autoload/airline/themes/` directory; set `g:airline_theme` to `adwaita_amoled`. Airline itself is optional. |
| Rofi | Add `@import "/absolute/path/to/Adwaita-AMOLED/extra/rofi/adwaita-dark.rasi"` to `config.rasi`, or pass that file with `-theme`. |
| Zsh | Source `extra/zsh/.zshrc` from your existing `.zshrc`, after any optional highlighting/autosuggestion plugins. This changes prompt, completion styling and the title hook as well as plugin colors. |
| Wallpaper | Select `extra/wallpaper/blackmount.png` in background settings. |

For Neovim, add to **your existing** `init.vim`:

```vim
set termguicolors
colorscheme adwaita-amoled
let g:airline_theme = 'adwaita_amoled'
```

Or use the corresponding lines in **your existing** `init.lua`:

```lua
vim.opt.termguicolors = true
vim.cmd('colorscheme adwaita-amoled')
vim.g.airline_theme = 'adwaita_amoled'
```

Do not create a second init file alongside the one you already use.

For Qt, copy the palettes and optional QSS, then select them through the matching
Qt configuration app as explained in [Qt selection](#qt-selection):

```bash
amoled_config="${XDG_CONFIG_HOME:-$HOME/.config}"
for amoled_qt in qt5ct qt6ct; do
  mkdir -p "$amoled_config/$amoled_qt/colors" "$amoled_config/$amoled_qt/qss"
  cp "$amoled_theme/extra/$amoled_qt/colors/Adwaita-AMOLED.conf" "$amoled_config/$amoled_qt/colors/"
  cp "$amoled_theme/extra/$amoled_qt/qss/fusion-simple-scrollbar.qss" "$amoled_config/$amoled_qt/qss/"
done
```

## Selected Flatpak applications

Flatpak setup is **optional and per application**. It requires Flatpak and an
already installed GTK application. It runs as your normal user, separately from
system-wide installation:

```bash
./install.sh install --components gtk,libadwaita --flatpak APP_ID --dry-run
./install.sh install --components gtk,libadwaita --flatpak APP_ID --yes
# Repeat --flatpak for additional application IDs.
```

Replace `APP_ID` with an actual ID such as the one shown by `flatpak list --app`.
The user installation remains in `DATA/themes/Adwaita-AMOLED`. For each selected
application, setup:

1. Queries the installed app/runtime locations through Flatpak. It checks the
   app's standard bundled GTK4 libraries first, then its runtime's libraries.
   GTK's upstream shared-library version convention determines the GTK version;
   no host GTK library is used to choose a sandbox stylesheet.
2. Creates a managed theme selection in
   `~/.var/app/APP_ID/config/gtk-3.0/settings.ini`. Desktop/portal settings may
   take precedence over GTK3's config, so keep the desktop GTK theme selected too.
3. For GTK4, manages its own import in
   `~/.var/app/APP_ID/config/gtk-4.0/gtk.css`, selecting modern CSS on GTK 4.16+
   and legacy CSS on older GTK4. Its other custom CSS is retained.
4. Adds two **read-only**, app-specific filesystem entries: the XDG theme
   subdirectory, which Flatpak also maps into the app's data directory, and the
   absolute installed theme path used by the CSS import. Flatpak's own parser
   encodes the entries. Existing permissions/environment settings are retained.

No global Flatpak override is changed. No `GTK_THEME` environment variable is
exported. No app/runtime is installed or downloaded. Qt and other non-GTK Flatpak
applications need their own toolkit integration.

If a runtime uses unversioned/repacked GTK libraries or an unusual loader path,
check its actual GTK version and choose explicitly:

```bash
./install.sh install --components gtk --flatpak APP_ID=modern --yes
./install.sh install --components gtk --flatpak APP_ID=legacy --yes
./install.sh install --components gtk --flatpak APP_ID=gtk3 --yes
```

`gtk3` installs theme access and GTK3 selection without a GTK4 override. A detected
older GTK4 library refuses forced modern CSS. Custom loaders, command-line
sandbox options and app-supplied CSS can still need app-specific testing.

An existing mapping of host `xdg-config` or `xdg-config/gtk-4.0` into the app can
hide its own per-app stylesheet. Setup detects such mappings and stops for you
to resolve them first. It also refuses a custom `XDG_CONFIG_HOME` override rather
than writing a configuration the app would never read. Do not add the old global
host-config sharing command on top of this per-app setup.

The Flatpak installation/override directory honors `FLATPAK_USER_DIR`. State and
before-images remain in the normal user installer history. To remove **only** a
selected app's managed configuration and theme permission entries:

```bash
./install.sh uninstall --flatpak APP_ID --dry-run
./install.sh uninstall --flatpak APP_ID --yes
```

This keeps the native installation and other selected apps. Uninstalling the
whole user installation also undoes all tracked Flatpak setup. Later unrelated
Flatpak/Flatseal permission and environment changes survive update and undo;
a later change to one of our exact theme permission entries stops with a
conflict instead of overwriting it. Remove tracked setup for an uninstalled app
before updating the remaining apps; undo does not require the app to be installed.

## System-wide theme and root GTK4

This is a separate scope with its own history. Review the command's plan, then
run with administrative privileges:

```bash
sudo ./install.sh install --system --dry-run
sudo ./install.sh install --system --yes
```

It copies the included runtime to
`/usr/local/share/themes/Adwaita-AMOLED`. Installed files/directories are owned by
root, files are readable by all users and directories are traversable. Existing
files, file modes and ownership are backed up; undo restores them. Source
executability is retained. Files are copied rather than linked into a user's
home directory. New empty directories may remain after undo.

This makes the theme available for selection by all users and conventional root
GTK applications. It does not select the theme for every account, change GDM or
configure all users' libadwaita overrides. Many administrative apps already draw
their GUI as the normal user and only elevate a backend.

For a GUI that actually runs as root, root's GTK4/libadwaita override can also be
selected explicitly:

```bash
sudo ./install.sh install --system --root-gtk4 --dry-run
sudo ./install.sh install --system --root-gtk4 --yes
```

This manages an import in root's own `~/.config/gtk-4.0/gtk.css`, using the root
home recorded in the system account database (normally `/root`). It ignores
`sudo`'s inherited user HOME/XDG paths, preserves root's custom CSS, and references
the root-owned shared theme. GTK2/3 theme selection for root remains separate.
This option does not enable root GUI access to Wayland/X11 or bypass authentication.

```bash
sudo ./install.sh update --system --yes
sudo ./install.sh status --system
sudo ./install.sh uninstall --system --dry-run
sudo ./install.sh uninstall --system --yes
```

System state/backups live under `/var/lib/adwaita-amoled` with private records.
The user and system scopes update/undo independently; removing one leaves the
other's files and history intact. Desktop activation, user app components and
Flatpak setup run separately without sudo. For packaging/tests,
`--system-root /absolute/staging-directory` places all system destinations below
that directory; it is normally left as `/` and still requires root ownership.

## Coverage and other limits

Snap and other sandboxes need their own setup; Flatpak filesystem options do not
apply to them. App-supplied CSS and explicit custom config-file/loader arguments
can override theme settings.

Firefox's `widget.gtk.libadwaita-colors.enabled` preference can affect its color
integration; change it yourself if needed. Browser preferences, Brave, actual
login sessions, physical OLED behavior and GPU drivers are not configured or
established by the installer tests.

The native automated checks cover actual GTK/libadwaita loading on GTK 4.14 and
4.24, Kitty, bat, Neovim, Rofi and Zsh, plus configuration preservation,
update/undo and failure recovery. Alacritty imports are structurally checked
with a TOML parser; Qt palette copies are verified. These checks supplement the
existing [theme consumer tests](tests/README.md), rather than establish every
possible desktop/app setup.


## Loading references

The installation layout and GTK4 loader follow [GTK CSS provider documentation](https://docs.gtk.org/gtk4/class.CssProvider.html)
and [GTK's runtime environment documentation](https://docs.gtk.org/gtk4/running.html).
The override's scope follows [libadwaita's appearance guidance](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html).
GNOME Shell's duplicate-directory check follows the User Themes extension's
[theme-directory search order](https://github.com/GNOME/gnome-shell-extensions/blob/51.0/extensions/user-theme/util.js).
Flatpak limitations follow its [sandbox permissions guidance](https://docs.flatpak.org/en/latest/sandbox-permissions.html).
These explain loader behavior; they do not establish compatibility with every app.
