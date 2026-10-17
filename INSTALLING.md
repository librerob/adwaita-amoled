# Installing Adwaita-AMOLED

The installer uses the included, already compiled theme. It requires Linux,
Bash and **Python 3.11 or newer**. Run it as your normal desktop user, without
`sudo`. No compiler, rsync, network access or Python package installation is
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
native GTK version, detected desktop, selected components, missing/edited files,
changed managed desktop preferences, state and backup locations. They return a
nonzero status for detected differences or an interrupted transaction. They do
not render your applications or diagnose hardware.

### Backups and preservation

State lives in `$XDG_STATE_HOME/adwaita-amoled` (default
`~/.local/state/adwaita-amoled`). `state.json` records original bytes, permissions,
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

## Flatpak and other limits

Setup changes **native host** configuration. Flatpak apps have independent
runtimes, theme extensions, paths and permissions; the host GTK version may not
match their GTK. A host file import can be inaccessible inside the sandbox.
The installer does not change Flatpak permissions or promise sandbox coverage.
Prefer a matching runtime theme extension where available; per-app overrides
need separate runtime-aware testing. The same caution applies to Snap and other
sandboxes, custom config-file command-line options, and app-supplied CSS.

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
