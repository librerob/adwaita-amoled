<p align="center">
  <img src="./extra/logo/logo.png" alt="Adwaita AMOLED Logo" width="320">
</p>
<h1 align="center">Adwaita AMOLED</h1>
<p align="center">
A true black, AMOLED-optimized take on the classic Adwaita design.
</p>
<p align="center">
<img src="https://img.shields.io/badge/GTK2-✓-black">
<img src="https://img.shields.io/badge/GTK3-✓-black">
<img src="https://img.shields.io/badge/GTK4-✓-black">
<img src="https://img.shields.io/badge/libadwaita-✓-black">
<img src="https://img.shields.io/badge/GNOME_Shell-46_%7C_51-black">
<img src="https://img.shields.io/badge/XFCE-✓-black">
<img src="https://img.shields.io/badge/Cinnamon-✓-black">
<img src="https://img.shields.io/badge/Openbox-✓-black">
<img src="https://img.shields.io/badge/Qt5ct-✓-black">
<img src="https://img.shields.io/badge/Qt6ct-✓-black">
</p>

---

<p align="center">
  <img src="./extra/screenshot/screenshot.png" alt="Adwaita AMOLED Screenshot">
</p>

<p align="center">
  <img src="./extra/screenshot/screenshot2.png" alt="Adwaita AMOLED Screenshot">
</p>


---

## Features

- True AMOLED base (`#000000`) with layered depth
- Clear visual hierarchy across all widget states, unfocused, hover, active
- Correct GTK3 widget rendering: checkboxes show ✓, radio buttons show ●, indeterminate states work
- Refined XFCE panel with accent underline focus indicator, no flat white blocks
- Complete GTK2 theme via the murrine engine, fully styled across all widget classes
- GTK4 + libadwaita color overrides included
- GNOME Shell 46 and 51 themes based on their matching upstream defaults, with an AMOLED palette
- Cinnamon shell theme, Openbox theme, and Metacity window decorations included
- Qt5ct and Qt6ct color schemes aligned with the GTK palette

See [tested upstream versions and coverage limits](COMPATIBILITY.md) for the
latest compatibility review. See the [color readability audit](COLOR_READABILITY.md)
for color roles, native measurements and the limits of contrast checks. The
[repository-wide color follow-up](COLOR_COMPLETENESS.md) records compound-state
fixes and the expanded file/paint review.

---

## Installation

The compiled theme is included. Choose the installer or the manual route below.
The installer needs Linux, Bash and **Python 3.11 or newer**; manual installation
needs no Python or compiler. GTK2 apps require your distribution's Murrine engine.

### Installation script

```bash
git clone https://github.com/librerob/adwaita-amoled.git
cd adwaita-amoled
./install.sh
```

The terminal wizard lets you choose GTK/libadwaita and optional app themes,
shows the exact paths and desktop preferences, and backs up changes for undo.
Run it as your normal user, without `sudo`. If you previously installed into
`~/.themes/Adwaita-AMOLED`, move that directory outside `~/.themes` first and
keep it as a backup, so it cannot shadow the updated installation.

For a preview without changes, or a noninteractive installation:

```bash
./install.sh install --components gtk,libadwaita --activate --dry-run
./install.sh install --components gtk,libadwaita --activate --yes
```

The theme goes to `~/.local/share/themes/Adwaita-AMOLED` by default. The native
GTK4/libadwaita option manages one import in `~/.config/gtk-4.0/gtk.css`, selects
the appropriate stylesheet for your installed GTK version, and preserves custom
CSS. Restart apps after updating. XDG directory overrides are honored.

See [the complete installation guide](INSTALLING.md) for **every component,
destination, setting, prerequisite, backup and undo behavior**. In particular,
Qt palettes need selection in qt5ct/qt6ct. Flatpak and system-wide installation
are separate, explicit options described below.

```bash
# Run from a newer downloaded checkout/release to update:
./install.sh update --dry-run
./install.sh update --yes
./install.sh status
# Undo the tracked installation while retaining backups:
./install.sh uninstall --yes
```

### Manual installation

From the extracted theme/repository directory, copy the compiled theme folders:

```bash
amoled_theme="${XDG_DATA_HOME:-$HOME/.local/share}/themes/Adwaita-AMOLED"
mkdir -p "$amoled_theme"
cp -R cinnamon gnome-shell gtk-2.0 gtk-3.0 gtk-4.0 metacity-1 openbox-3 extra "$amoled_theme/"
cp index.theme LICENSE "$amoled_theme/"
```

Back up an existing installation first, and keep only one active copy named
Adwaita-AMOLED across `~/.themes` and the XDG theme directory. Select it in your
desktop's Appearance settings. For **GTK4/libadwaita**, follow the
[manual override instructions](INSTALLING.md#gtk4-and-libadwaita-overrides), which
back up your existing config and select the entry point for your GTK version.
[Manual extras](INSTALLING.md#manual-extras) cover each supplied application.
Manual copying is updated/undone manually; the script only undoes tracked changes.

### Optional Flatpak and system-wide setup

For an already installed GTK Flatpak app, configure that app's own GTK stylesheet
and grant read-only access to the theme:

```bash
./install.sh install --components gtk,libadwaita --flatpak APP_ID --dry-run
./install.sh install --components gtk,libadwaita --flatpak APP_ID --yes
# Undo only this app's setup:
./install.sh uninstall --flatpak APP_ID --yes
```

Replace `APP_ID` with the app's ID. Its GTK library version selects modern/legacy
CSS independently of the host. Unusual runtimes can need an explicit mode.
See [Flatpak configuration and permission undo](INSTALLING.md#selected-flatpak-applications).

To make a root-owned copy available system-wide:

```bash
sudo ./install.sh install --system --dry-run
sudo ./install.sh install --system --yes
# Undo the separate system installation:
sudo ./install.sh uninstall --system --yes
```

This installs into `/usr/local/share/themes/Adwaita-AMOLED`, with independent
backups under `/var/lib/adwaita-amoled`. Root GTK4/libadwaita CSS is an additional
explicit `--root-gtk4` option. [System-wide and root details](INSTALLING.md#system-wide-theme-and-root-gtk4)
explain ownership, selection and scope. User/Flatpak setup runs without sudo.

## GNOME Shell

The included Shell themes target **GNOME Shell 46.x and 51.x**, based on upstream
**46.10 and 51.1** respectively. The installer detects the local Shell version
and installs the matching stylesheet; other major versions are unverified.
Install the [User Themes extension](https://extensions.gnome.org/extension/19/user-themes/)
and log in again if needed, then choose `shell` in the wizard with desktop
activation, or select Adwaita-AMOLED in the extension's settings.
[Shell details](gnome-shell/README.md) explain its scope and rebuilding. The
logged-in Shell is themed; other Shell major versions and GDM are outside its
verified scope.

For manual installation on GNOME 46, copy `gnome-shell-46.css` over
`gnome-shell.css` **inside the installed theme's `gnome-shell/` directory**, keeping
the complete `assets/` directory beside it. The source archive's default entry
is GNOME 51; it must not be selected unchanged on GNOME 46. Toggle User Themes
off/on, or log out and back in, after changing the installed stylesheet.

## Extras

Choose these names in the wizard or `--components` list:

| Component | Effect |
|---|---|
| `qt` | Install Qt5ct/Qt6ct palettes and optional scrollbar QSS; select through Qt settings |
| `kitty` | Include terminal colors, cursor and tab settings in the existing config |
| `alacritty` | Add a theme import to current TOML configuration |
| `bat` | Install/select the syntax theme and rebuild bat's cache |
| `nvim` | Install/select the Neovim and optional Airline themes |
| `rofi` | Import the launcher theme |
| `zsh` | Source prompt, completion and optional plugin colors after existing config |
| `wallpaper` | Copy the wallpaper for selection in background settings |

[INSTALLING.md](INSTALLING.md#every-component-and-destination) explains the exact
paths and effects. Optional applications/plugins are not installed automatically.

---

## Building and testing

Developers editing GTK source need GLib's resource compiler. Ordinary
installation does not require a build:

```bash
# Debian / Ubuntu
sudo apt install libglib2.0-dev
# Arch / Artix
sudo pacman -S glib2
```

```bash
./build.sh
./build.sh --install
```

`--install` builds the GTK bundles, then delegates to the reversible installer
with `--yes`. Additional installer options can follow `--install`. It requires
Python 3.11+ and uses the same GTK4 import and backups as `install.sh`.
After editing `src/`, rebuild and commit the updated `gtk.gresource` bundles
together with their source changes.

The GNOME Shell CSS is also included precompiled. After changing its Sass
palette, rebuild it separately with `./gnome-shell/build.sh` (requires `sassc`).

Build an installer-enabled runtime archive (without source GTK files or tests):

```bash
python3 tools/package.py /tmp/Adwaita-AMOLED-installer-preview.tar.gz
```

The archive includes per-file checksums; a separate SHA-256 file is written beside
it. This creates local files and does not publish a GitHub release.

The repository's regression checks and their prerequisites are documented in
[tests/README.md](tests/README.md). GitHub Actions runs them on pull requests.

---

## Wallpaper

A matching wallpaper is included at `extra/wallpaper/blackmount.png`.

---

## Color Palette

| Token | Hex | Role |
|---|---|---|
| Background | `#000000` | Window base, AMOLED black |
| Surface 1 | `#0f0f0f` | Cards, lists |
| Surface 2 | `#141414` | Popovers, tooltips |
| Hover | `#1a1a1a` | Hover state |
| Control border | `#808080` | Identifying control outlines |
| Decorative border | `#2a2a2a` | Nonessential separators and depth |
| Text accent | `#8ab4f8` | Readable accent text, links and focus |
| Filled GTK accent | `#2d6be0` | Selected surfaces with white text |
| Filled hover | `#2862cf` | Hovered selections/controls with white text |
| Foreground | `#ffffff` | Primary text |
| Dim | `#a0a0a0` | Readable secondary text |

White on the filled GTK accent has approximately 4.89:1 contrast. Extras that
use the pale `#8ab4f8` as a text background use black text (9.96:1).
Success surfaces use black text on `#26a269` (approximately 6.45:1).

### Why these colors

The palette separates standalone accent text from filled controls so that both
remain readable on AMOLED surfaces:

| Use | Foreground / background | Defined sRGB contrast |
|---|---|---|
| Accent text and links on black | `#8ab4f8` / `#000000` | 9.96:1 |
| Accent text on a raised surface | `#8ab4f8` / `#141414` | 8.74:1 |
| Filled blue controls | `#ffffff` / `#2d6be0` | 4.89:1 |
| Pale selections in applicable extras | `#000000` / `#8ab4f8` | 9.96:1 |

White text on the pale blue would reach only 2.11:1, so pale selections use black
labels. Dark blue buttons keep white labels. Focus/identifying graphics are
checked separately from text; disabled states and decorative separators have
different roles. GNOME Shell retains the system-selected accent hue and uses
state-specific filled colors.

These choices address measured contrast issues while retaining AMOLED black and
Adwaita's layout. They are not a claim that one blue is universally best, that
all users/displays see colors identically, or that contrast ratios alone prove
complete accessibility. The [readability audit](COLOR_READABILITY.md) and
[broader color follow-up](COLOR_COMPLETENESS.md) document native state tests,
intentional exceptions and remaining limits.

---

## Structure

```
Adwaita-AMOLED/
├── cinnamon/               Cinnamon shell theme
├── gnome-shell/            GNOME Shell 46/51 themes, assets and Sass source
├── gtk-2.0/                GTK2 theme (murrine engine)
├── gtk-3.0/                GTK3 theme
├── gtk-4.0/                GTK4 theme
├── metacity-1/             Metacity / Muffin window decorations
├── openbox-3/              Openbox window manager theme
├── extra/
│   ├── alacritty/          Alacritty terminal theme
│   ├── kitty/              Kitty terminal theme
│   ├── libadwaita/         Native GTK4 entry points, managed by install.sh
│   ├── logo/               Theme logo
│   ├── nvim/               Neovim colorscheme and airline theme
│   ├── qt5ct/              Qt5 color scheme
│   ├── qt6ct/              Qt6 color scheme
│   ├── rofi/               Rofi launcher theme
│   ├── screenshot/         Preview image
│   ├── wallpaper/          Matching wallpaper
│   └── zsh/                Zsh autosuggestions & syntax highlighting config
├── install.sh              Interactive/reversible user installer
├── tools/                  Installer implementation and migration hashes
├── INSTALLING.md           Complete installation and undo guide
└── index.theme
```

---

## Philosophy

Minimal, readable, and actually usable.
No washed-out grays, no invisible states.
