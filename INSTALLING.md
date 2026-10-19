# Installing Adwaita-AMOLED

The installer is a **Bash script** using GNU coreutils and `flock` (util-linux),
normally already installed on Linux desktops. It copies
already compiled files: no Python, compiler, downloads, package installation,
backup database or undo history is required. GTK2 applications also
need your distribution's Murrine engine (`gtk2-engines-murrine` on Debian/Ubuntu).

## Start here

Before applying, setup lists the selected file destinations. At the review,
enter **d** for optional explanations of how to use the selected extras; this
does not apply any changes. After installation, a short message points to the
installed copy of this guide, so the paths and app setup examples remain available.

Extract the release archive or clone the repository, then run:

```bash
./install.sh
```

In a terminal this opens guided setup:

1. **Install/update** offers native GTK4/libadwaita styling, desktop selection,
   matching supported GNOME Shell styling and optional application extras.
   Supported app appearance preferences are set to dark automatically, without
   an extra question, and listed in the final review.
2. **Remove** removes the theme and its owned native GTK4 links, with optional extras.
3. **Help** explains setup; **Advanced options** covers a shared system theme
   and selected-app Flatpak configuration.
4. **Accent color** chooses blue (default), yellow, gold, purple, green, red,
   orange or pink, then returns to the main menu. Continue with Install/update.

Numbered choices need only Enter or a number. Setup shows destinations and
existing GTK4 override paths before its final **Apply / Cancel / Preview**
choice. Enter at that final question cancels. Preview prints operations and
exits without applying them; rerun setup when ready. EOF or Ctrl-C before
confirmation also leaves the installation untouched.

The default user destination is
`${XDG_DATA_HOME:-$HOME/.local/share}/themes/Adwaita-AMOLED`. GTK4 setup defaults
to keeping existing overrides when any of the four override paths already
exist. New GTK4 setup is offered by default; an unknown GTK version lets you
choose its version range or skip, rather than guessing. Shell activation is
offered only for 46/51 when desktop selection and User Themes are available.
Unknown desktops or unavailable settings tools use manual Appearance selection.

Explicit command-line options always run without questions. To apply the
native GTK4 override and select supported desktop preferences directly:

```bash
./install.sh -l --activate
```

Run user setup **without sudo**. `--dry-run` prints operations without applying
them, and `--help` lists the options. To install without menus, run
`./install.sh install`. Bare `./install.sh` also uses noninteractive installation
when stdin or stdout is not a terminal, so existing automation does not hang.
Both set supported app appearance preferences to dark during user installation.
`./install.sh --interactive` forces guided setup, requires a terminal, and must
be used without other options.

The Advanced shared-system option opens a separate administrator setup with
`sudo` (which may ask for your password). It offers a real copy in
`/usr/local/share/themes` or `/usr/share/themes`, plus the optional root-owned
link for the former. Its review still requires confirmation. Personal GTK4 and
app configuration is done separately as your normal desktop user.

Flatpak menus list installed apps and let you select each app's GTK3 or GTK4
runtime mode. This can differ from the host; skip if unsure. Removing selected
Flatpak styling keeps installed theme files, matching the command-line behavior.
Before removing the theme itself, remove any selected-app Flatpak styling under
Advanced options. The installer does not save which options you used previously.

**Rerunning replaces the installed theme.** `-l` replaces these four paths in
`${XDG_CONFIG_HOME:-$HOME/.config}/gtk-4.0` with symlinks to the installed theme:
`gtk.css`, `gtk-dark.css`, `libadwaita-tweaks.css` and `assets`.
This replaces existing overrides, including custom ones, without backups.
Other files in that directory, including `settings.ini`, are left alone.
Restart GTK applications after installation.

The installer copies only files listed in `runtime-files.txt`, whether run from
a checkout or a release archive. This includes compiled GTK/Shell styles,
runtime assets, app extras, the wallpaper, guides and license/provenance notices.
The logo, screenshots, palette templates and GTK/Shell development sources are
not installed. For rebuilding, use a Git checkout or GitHub's source archive.

## Accent colors

New installations default to blue. Choose **Accent color** in guided setup, or
specify a preset directly:

```bash
./install.sh --accent gold -l --activate
./install.sh --accent green --extras qt,kitty,nvim
sudo ./install.sh --system --accent purple
```

The choices are **blue, yellow, gold, purple, green, red, orange and pink**.
The selected preset covers GTK2/3/4, the optional libadwaita override, Cinnamon,
window decorations, Shell 46/51 and the supplied application themes. Semantic
error/success/warning and terminal/syntax colors keep their meanings. Main
surfaces remain black. See [measured colors and limits](ACCENT_COLORS.md).

Only one preset is installed at a time, named **Adwaita-AMOLED**. Precompiled
files under `accents/` supply the changed files; shared assets are copied once.
Users need no compiler or Python. Variant manifests are checked before copying
and on the staged theme. The full collection of overlays is not installed.

Rerunning from a newer download retains the valid installed `accent-name`
marker unless `--accent` selects another color. Older installations without a
marker use blue. To return to blue, run `./install.sh --accent blue`.
Rerun with the same optional extras to refresh their copied app snippets;
GTK4/Flatpak links already referencing this theme follow the changed theme files.
Restart apps and reload Shell/Cinnamon as appropriate. Separate user and system
installations each retain their own color. Shared-system guided setup also has
an Accent color choice.

GNOME Shell 46 and 51 match the selected preset for **all eight colors,
including blue**, regardless of GNOME Settings' system accent.
This does not change the system accent setting or application-owned accent
preferences. Other Shell major versions remain unverified.

Before replacing a theme directory, the script checks essential files and
prepares a complete temporary copy beside the destination. Release archives
also have their per-file checksums verified before copying and again on the
staged copy. Ordinary preparation/rename failures and tested catchable signals
keep or restore the previous theme. Temporary staging is removed afterward;
there is no saved backup history. Directory locks reject concurrent installers
without creating lock files.

The script normally installs to the XDG location above and creates
`~/.themes/Adwaita-AMOLED` as a compatibility link to it: GTK2 does not discover
themes in `XDG_DATA_HOME/themes`. If a regular legacy directory already exists,
the default user install refreshes that copy instead, provided it contains only
known runtime files. Git checkouts and unlisted local data are kept unchanged.
A legacy link pointing
elsewhere is reported before changing installed files; it is never overwritten.
Default removal also removes a matching compatibility link. `--dest DIR`
selects a different theme parent and updates only that location, without adding
this link. Run from an extracted download/checkout outside the installed theme
directory.

## Update and remove

Download/extract a newer release and rerun the same command with the options
you want, for example:

```bash
./install.sh -l --activate
```

For GTK4 links and app extras, repeat your selections on each update. The
former `install`, `update`, `--yes` and
`--components gtk,libadwaita` spellings are accepted for convenience, but there
is no state tracking. State/backups from the old Python installer are left
untouched and never consulted. Known theme files are replaced, including local
edits to those files. A `.git` directory/file/link or unlisted local files stop
both replacement and removal before any theme is changed. This also protects an
old clone under `~/.themes/Adwaita-AMOLED`. Move the checkout or local data to a
safe location outside the installation destinations, then rerun setup. The
installer does not move/delete that data or create an automatic backup.
The installed runtime manifest allows obsolete theme assets from older releases
to be updated normally; it must contain valid relative runtime paths.
Do not run the old installer's undo after switching to this script.

To remove the user theme and its owned native GTK4 links:

```bash
./install.sh --remove
```

Removal deletes the theme; it does not restore earlier files or desktop
preferences. GTK4 removal only unlinks symlinks pointing into this installed
theme, leaving replacement custom CSS and links to other themes alone. This
cleanup happens even without `-l`; that option remains accepted for older
commands. Empty configuration directories are left in place. System-wide
removal leaves personal GTK4 configuration alone, and removing selected Flatpak
styling keeps native links and the installed theme. Choose another desktop theme in
Appearance settings. Include `--extras LIST` to remove those copied app theme
files too; existing app settings are not reset.

Theme directories are replaced separately, and extras, GTK4 links and desktop
preferences are applied afterward; this is not an all-or-nothing transaction
across every destination. SIGKILL, power loss and failing hardware cannot be
guaranteed recoverable. If a restore itself fails, the error reports where the
previous theme was retained rather than deleting it. Resolve the underlying
failure before retrying.

## GTK4 entry point

With `-l`, the script checks the installed GTK4 package version using pkg-config
or the distribution's package manager (dpkg, RPM, pacman or apk). GTK 4.16+
uses `gtk-modern.css`; older GTK4 uses `gtk.css`. Unknown versions require an
explicit selection after checking your GTK package version:

```bash
./install.sh -l --gtk4-mode legacy
# For GTK 4.16 or newer instead:
./install.sh -l --gtk4-mode modern
```

Libadwaita is configured through user CSS, rather than an official theming API.
Do not set GTK_THEME globally. App-specific styling can still override parts
of the theme. Set a dark appearance in your desktop/app when available: editors
such as GNOME Text Editor select their document/syntax colors separately, and
can retain a white editing canvas while following a light system preference.
The theme does not replace an application's syntax color scheme.

## Desktop activation

`--activate` selects these preferences for the current `XDG_CURRENT_DESKTOP`:

| Desktop | Preferences |
|---|---|
| Cinnamon | GTK theme, Muffin window theme and Cinnamon shell theme |
| GNOME / Budgie | GTK theme |
| MATE | GTK theme and Marco window theme |
| Xfce | GTK theme through xfconf; Xfwm4 decorations are unchanged |

The script does not install icons, cursors, fonts or missing desktop packages.
For other desktops, select the theme manually. Openbox selection is manual.

User installation/update automatically sets supported application appearance
preferences to dark, with no extra question or flag. Both the guided review and
`--dry-run` show the selected settings before they are written. This also applies
without `--activate`, which separately selects the desktop theme. The former
`--prefer-dark` flag is accepted for compatibility but is no longer needed.

| Session | App appearance settings, when available |
|---|---|
| GNOME / Budgie | `org.gnome.desktop.interface color-scheme` |
| Cinnamon / MATE / Xfce | `org.x.apps.portal color-scheme` and `org.gnome.desktop.interface color-scheme` |

The latter sessions can use either the XApp or GTK settings portal, depending
on the distribution. Their available supported keys are set together to
`prefer-dark`, and the review lists each key. Missing, unreadable or locked keys
are skipped. If none are available, theme installation continues and reports
that app appearance was kept unchanged. A write failure is reported without
failing theme installation. Unknown desktops are not guessed. This does not
install or repair a missing portal service, and an application's own theme can
override the preference.

This is a user-wide preference for supporting apps, rather than Firefox-only
configuration. It remains selected after removing the theme; removal has no
saved preference history. Removal and shared `--system` installation do not
change any personal app appearance preferences.
To return to no preference, use your desktop's Appearance settings or set the
listed `color-scheme` keys back to `default`. To restore a previous explicit
light preference instead, select light appearance (`prefer-light`).

For the optional **GNOME Shell 46 or 51** theme:

```bash
./install.sh -l --shell --activate
```

Install/enable User Themes first. The script checks the installed Shell version,
uses its matching stylesheet and can enable/select User Themes with
`--activate`. The installed default entry follows a detected 46/51 version even
without `--shell`; otherwise it remains the bundled 51 default, which does not
establish compatibility. Other Shell majors remain unverified and explicit
`--shell` setup stops on them. `--shell-version 46` or `51` can select a variant
for staging; activation requires a matching local version. Reload User Themes
or log out/in after updating, especially on Wayland. GDM is not themed.

### Firefox dark appearance

Firefox's window decorations can follow the GTK/window theme while its tabs
and address bar remain light. With **System theme — auto**, Firefox also reads
the desktop's color preference through the settings portal. Selecting a dark
GTK theme alone does not necessarily change that preference. User installation
with this installer now sets supported preferences to dark automatically. Manual
theme copying/selection does not. The installer does not edit Firefox profile
settings.

In Firefox, open **Add-ons and themes → Themes** and enable **System theme —
auto**. On Linux Mint Cinnamon, open **Themes → Settings** and select
**Prefer dark mode** under **Dark mode**. On versions exposing the XApp setting,
the equivalent command, run as your normal desktop user without sudo, is:

```bash
gsettings set org.x.apps.portal color-scheme 'prefer-dark'
```

This preference applies to applications that honor it, including Firefox; it
does not recolor every application or website. To return to Mint's
**Let applications decide** setting:

```bash
gsettings set org.x.apps.portal color-scheme 'default'
```

Other desktops have their own appearance settings. For GNOME, select **Dark**
in **Settings → Appearance**. If you only want Firefox to change, enable its
built-in **Dark** theme instead of **System theme — auto**. An explicitly
selected **Light** theme can keep Firefox light despite a dark desktop
preference. Restart Firefox if the change is not picked up immediately.

Firefox renders much of its interface itself, so dark mode does not guarantee
the GTK theme's exact AMOLED colors. Ordinary websites control their own
styling, and Firefox's website appearance setting is separate from its toolbar
theme. Flatpak/Snap builds also depend on their sandbox's portal access.

The separate setting is used by [Mint's own dark-style selector](https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/cinnamon-settings/modules/cs_themes.py)
and exported by the [XApp settings portal](https://github.com/linuxmint/xdg-desktop-portal-xapp/blob/master/src/settings.c).

## Every extra and destination

All supplied extras are always included inside the installed theme. To also
copy app-specific theme files into the usual user locations, use:

```bash
./install.sh --extras qt,kitty,nvim
# Or copy all extras:
./install.sh --extras all
```

Missing destination folders are created. **These options copy theme files;
they do not edit your existing application settings.** Select/include the
copied theme using the app's own settings or the manual examples below.
`CONFIG` means `${XDG_CONFIG_HOME:-$HOME/.config}`, and `DATA` means
`${XDG_DATA_HOME:-$HOME/.local/share}`.

| Extra | Destination / selection |
|---|---|
| `qt` | `CONFIG/qt5ct` and `CONFIG/qt6ct`, under `colors/` and `qss/`. Select Adwaita-AMOLED in the matching qt5ct/qt6ct app. Enable the optional `fusion-simple-scrollbar.qss` for visible scrollbar and slider handles. No global Qt plugin variable is changed. |
| `kitty` | `CONFIG/kitty/themes/adwaita-amoled.conf`, or the corresponding `KITTY_CONFIG_DIRECTORY/themes/` location. Include that file in your active `kitty.conf`. |
| `alacritty` | `CONFIG/alacritty/themes/adwaita-amoled.toml`. Add it to `[general].import` in your active TOML config, preserving existing imports. |
| `bat` | `themes/adwaita-amoled.tmTheme` in bat's reported config directory, or beside `BAT_CONFIG_PATH`; defaults to `CONFIG/bat`. Rebuilds bat's cache if bat/batcat is installed. Select with `--theme=adwaita-amoled`. |
| `nvim` | `CONFIG/nvim/colors/` and `autoload/airline/themes/`, honoring `NVIM_APPNAME`. Select the colorscheme in your existing init.lua/init.vim. Airline itself is not installed. |
| `rofi` | `CONFIG/rofi/themes/adwaita-amoled.rasi`. Select it with `rofi -theme PATH` or import it from your existing config.rasi. |
| `zsh` | `CONFIG/zsh/adwaita-amoled.zsh`. Source it from your existing `$ZDOTDIR/.zshrc` or `~/.zshrc`; the script does not replace your shell config. |
| `wallpaper` | `DATA/backgrounds/Adwaita-AMOLED/blackmount.png`. Select it in background settings. |

Kitty's snippet includes cursor/tab settings and dimming. Zsh's snippet includes
prompt/completion/title-hook and optional plugin colors. Read the snippet before
sourcing it. Optional applications/plugins are not installed automatically.

## Manual installation

The compiled theme can also be installed manually. These commands do not require
Python or a compiler. Run them from the extracted theme/repository directory as
your normal user. GTK2 still needs Murrine.

### Theme files and desktop selection

Keep a backup of an existing installed theme before replacing its files. Avoid
keeping a second independent copy named Adwaita-AMOLED in `~/.themes`, because
different desktop components search the locations in different orders. The
compatibility link below exposes the same copy to GTK2. If that legacy path
already exists, inspect it and resolve any older copy/link before proceeding;
the example does not replace it.

```bash
amoled_data="${XDG_DATA_HOME:-$HOME/.local/share}"
amoled_theme="$amoled_data/themes/Adwaita-AMOLED"
mkdir -p "$amoled_theme"
cp -R cinnamon gnome-shell gtk-2.0 gtk-3.0 gtk-4.0 metacity-1 openbox-3 extra "$amoled_theme/"
cp index.theme LICENSE accent-name "$amoled_theme/"
mkdir -p "$HOME/.themes"
if [ ! -e "$HOME/.themes/Adwaita-AMOLED" ] && [ ! -L "$HOME/.themes/Adwaita-AMOLED" ]; then
  ln -s "$amoled_theme" "$HOME/.themes/Adwaita-AMOLED"
fi
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

On GNOME 46, after the manual copy above, select its matching stylesheet:

```bash
cp "$amoled_theme/gnome-shell/gnome-shell-46.css" "$amoled_theme/gnome-shell/gnome-shell.css"
```

Keep all `gnome-shell/assets/` files installed. On GNOME 51, the equivalent source
is `gnome-shell-51.css`. Toggle User Themes off/on after changing the installed
CSS, or log out and back in. The source default is 51 and must not be used
unchanged on 46. Neither variant is verified for other Shell major versions.

### GTK4 and libadwaita overrides

Manual copying replaces the active GTK4 override files. Back up the existing
directory first; custom CSS can be merged back afterward. Use **`gtk-modern.css`
for GTK 4.16+**, or **`gtk.css` for older GTK4**. Check the GTK4 package version
installed by your distribution; the relevant version is GTK, not GNOME's version.
The script performs this choice automatically with `-l` on supported package managers.

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
manual override, restore your own backup. The Bash installer keeps no undo history.

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

Flatpak setup is explicit and per application. Check the app runtime's GTK
version; it can differ from the host. Use `legacy` for GTK4 before 4.16,
`modern` for GTK4 4.16+, or `gtk3` for GTK3-only apps:

```bash
./install.sh --flatpak org.example.App=modern
```

Replace the example ID with an already installed app. The command grants only
that app read-only access to the installed theme. GTK4 modes replace the same
four override paths in `~/.var/app/APP_ID/config/gtk-4.0` with links to the theme.
GTK3 mode instead sets that app's GTK_THEME override. No global Flatpak override
is used and there is no automatic runtime-version guess.

To remove just that app's links and this theme-access permission, keeping the
host installation:

```bash
./install.sh --remove --flatpak org.example.App=modern
```

This revokes this theme path and removes matching theme links; it does not
restore historical permissions or overrides. Other permissions/environment
values are left alone. GTK3 removal unsets the GTK_THEME override for that app.
Do not remove the host theme while other apps still link to it.

## System-wide theme

```bash
sudo ./install.sh --system
# Remove it:
sudo ./install.sh --system --remove
```

This copies root-owned shared theme files into
`/usr/local/share/themes/Adwaita-AMOLED`; it does not edit the invoking user's
configuration or root's GTK4 overrides. `--system --dest /absolute/parent`
can stage another shared location. Run user GTK4/Flatpak/extras configuration
separately without sudo. Root GTK4 user CSS must be configured separately if
needed; a system theme alone does not force libadwaita to use it.

GTK2 also needs the root-owned theme exposed through its system theme location,
normally `/usr/share/themes`. For the default shared copy, use:

```bash
sudo ./install.sh --system --link /usr/share/themes
# Repeat both options to update or remove the shared link and copy:
sudo ./install.sh --system --link /usr/share/themes --remove
```

The link is `/usr/share/themes/Adwaita-AMOLED` and points to
`/usr/local/share/themes/Adwaita-AMOLED`. It does not point into your home folder.
Both the system copy and link must have root-owned parents protected from other
writers. Existing unrelated directories or links are preserved and reported as
conflicts. No user configuration is changed. A shared theme makes its files
available to root/other users; each application still needs theme selection,
and libadwaita does not automatically load another user's GTK4 override.

Alternatively, for a real copy directly in `/usr/share/themes`:

```bash
sudo ./install.sh --system --dest /usr/share/themes
```

## Release archive checks

Installer-enabled runtime archives include `ARCHIVE_CONTENTS.sha256`. From the
freshly extracted directory, `sha256sum -c ARCHIVE_CONTENTS.sha256` verifies the
payload. The script verifies this manifest automatically when present. A Git
checkout without a manifest still has its essential runtime files checked.
It does not download anything. Developers build archives with `python3 tools/package.py OUTPUT.tar.gz`;
Python is only a development/testing dependency.
