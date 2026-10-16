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
<img src="https://img.shields.io/badge/GNOME_Shell-51-black">
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
- GNOME Shell 51 theme based on the upstream 51.1 default, with an AMOLED palette
- Cinnamon shell theme, Openbox theme, and Metacity window decorations included
- Qt5ct and Qt6ct color schemes aligned with the GTK palette

See [tested upstream versions and coverage limits](COMPATIBILITY.md) for the
latest compatibility review. See the [color readability audit](COLOR_READABILITY.md)
for color roles, native measurements and the limits of contrast checks.

---

## Installation

GTK2 applications require the **Murrine** theme engine. On Debian/Ubuntu:

```bash
sudo apt install gtk2-engines-murrine
```

The compiled GTK3/GTK4 bundles are included, so cloning does not require a build.

```bash
# Clone the repo
git clone https://github.com/librerob/Adwaita-AMOLED.git ~/.themes/Adwaita-AMOLED
```

Then set the theme through your desktop's appearance settings, or via the terminal:

```bash
# GTK (XFCE / Cinnamon / GNOME)
gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-AMOLED"
```

For a Flatpak application, install a matching GTK theme extension if one is
available for its runtime. Otherwise, expose the cloned theme and the GTK
configuration to that application (replace `APP_ID` with its application ID):

```bash
flatpak override --user \
  --filesystem="$HOME/.themes:ro" \
  --filesystem=xdg-config/gtk-3.0:ro \
  --filesystem=xdg-config/gtk-4.0:ro \
  APP_ID
```

The GTK4 overrides below must also be copied if you use libadwaita applications.
Flatpak runtimes and desktop theme detection vary; exposing the directories
alone does not select a theme or install a missing theme engine in the sandbox.

> **Firefox users:** Open `about:config` and set `widget.gtk.libadwaita-colors.enabled` to `false`.

---

## GNOME Shell

The included Shell theme targets **GNOME Shell 51.x** and is based on the
upstream **51.1** default. Install the [User Themes extension](https://extensions.gnome.org/extension/19/user-themes/),
enable it, and select **Adwaita-AMOLED** in its settings. Selecting the GTK
theme does not activate the Shell theme. See [Shell installation and source
details](gnome-shell/README.md) for commands and update instructions.

This themes the logged-in Shell session, including the panel, overview, menus,
notifications, OSDs and dialogs. Other Shell major versions and the GDM login
screen are outside its verified scope. GNOME's selected accent hue is retained;
opaque accent fills are darkened by state to keep white labels readable.

---

## GTK4 & libadwaita

libadwaita apps ignore GTK themes by default. To apply the overrides:

```bash
mkdir -p ~/.config/gtk-4.0
cp ~/.themes/Adwaita-AMOLED/extra/libadwaita/gtk.css ~/.config/gtk-4.0/gtk.css
cp ~/.themes/Adwaita-AMOLED/extra/libadwaita/gtk-dark.css ~/.config/gtk-4.0/gtk-dark.css
mkdir -p ~/.config/gtk-4.0/assets
cp -r ~/.themes/Adwaita-AMOLED/extra/libadwaita/assets/. ~/.config/gtk-4.0/assets/
cp ~/.themes/Adwaita-AMOLED/extra/libadwaita/libadwaita-tweaks.css ~/.config/gtk-4.0/libadwaita-tweaks.css

```

For **GTK 4.16 or newer** (libadwaita 1.6 or newer), then select the modern
entry point:

```bash
cp ~/.themes/Adwaita-AMOLED/extra/libadwaita/gtk-modern.css ~/.config/gtk-4.0/gtk.css
```

Keep `gtk-dark.css` and `libadwaita-tweaks.css` from the first block beside it.
The modern entry point imports them and maps libadwaita's standalone text
variables to the AMOLED colors. This prevents dark accent, status and destructive
text when an application requests light mode over the black surfaces. Repeat
both blocks after updating the theme or running `build.sh --install`.
On GTK 4.14 and older, use only the first block; those releases cannot parse
CSS variables.

> **Chromium / Brave:** recent builds prefer GTK4 on GNOME under Wayland (elsewhere it is opt-in via `--gtk-version=4`), so the GTK4 part of the theme matters there too. Choose the GTK option in the browser's Appearance settings. The `libadwaita-tweaks.css` you copy above is a copy, not a link: after updating the theme, copy it again and fully restart the browser.

---

## Qt (qt5ct / qt6ct)

```bash
# Qt5
mkdir -p ~/.config/qt5ct/colors
cp ~/.themes/Adwaita-AMOLED/extra/qt5ct/colors/Adwaita-AMOLED.conf ~/.config/qt5ct/colors/

# Qt6
mkdir -p ~/.config/qt6ct/colors
cp ~/.themes/Adwaita-AMOLED/extra/qt6ct/colors/Adwaita-AMOLED.conf ~/.config/qt6ct/colors/
```

Then open `qt5ct` / `qt6ct`, go to **Appearance → Color scheme**, and select **Adwaita-AMOLED**.

Install the corresponding `qt5ct` / `qt6ct` platform-theme plugin. If your
desktop does not already select it, launch an application with the matching
Qt version's integration:

```bash
QT_QPA_PLATFORMTHEME=qt5ct your-qt5-application
QT_QPA_PLATFORMTHEME=qt6ct your-qt6-application
```

Choose the appropriate value for each application; one global value does not
select both plugins. KDE and other desktops may already provide their own Qt
integration, which you should configure through their appearance settings.

---

## Extras

Additional themes are included in the `extra/` folder:

| Extra | Description | How to apply |
|---|---|---|
| **Alacritty** | Terminal color scheme aligned with the palette | Import the provided TOML; see [Alacritty setup](#alacritty) |
| **Kitty** | Terminal color scheme | Include the `.conf` file in your `kitty.conf` |
| **bat** | Syntax-highlighting theme | See [bat setup](#bat) below |
| **Neovim** | Colorscheme and airline theme | See [Neovim setup](#neovim) below |
| **Qt5ct / Qt6ct** | Full color schemes | See [Qt setup](#qt-qt5ct--qt6ct) above |
| **Rofi** | Matching launcher theme | Pass the theme with `-theme` or set it in your config |
| **Zsh** | Prompt, completion and optional plugin colors | See [Zsh setup](#zsh) |

All extras follow the same AMOLED palette and accent system as the GTK theme.

### Alacritty

For recent Alacritty versions (tested with 0.15.1), add this import to your
`alacritty.toml`, merging it into an existing `[general]` table if necessary:

```toml
[general]
import = ["~/.themes/Adwaita-AMOLED/extra/alacritty/alacritty.toml"]
```

### bat

```bash
mkdir -p ~/.config/bat/themes
cp ~/.themes/Adwaita-AMOLED/extra/bat/themes/adwaita-amoled.tmTheme ~/.config/bat/themes/
bat cache --build
```

Add `--theme="adwaita-amoled"` to your existing `~/.config/bat/config`.
On distributions that name the command `batcat`, use `batcat cache --build`.

### Zsh

The prompt and completion configuration works without highlighting plugins.
For autosuggestions and syntax colors, install `zsh-autosuggestions` and
`fast-syntax-highlighting` using your distribution or plugin manager, and load
them **before** sourcing this snippet:

```zsh
# Load your optional plugins above this line.
source ~/.themes/Adwaita-AMOLED/extra/zsh/.zshrc
```

The snippet declares its highlighting array when the plugin is absent and
registers a title hook without replacing other `precmd` hooks. Completion is
initialized only in interactive shells, and existing completion setups are
preserved.

### Neovim

Use Neovim 0.9 or newer and a true-color terminal.

```bash
mkdir -p ~/.config/nvim/colors
cp ~/.themes/Adwaita-AMOLED/extra/nvim/colors/adwaita-amoled.vim ~/.config/nvim/colors/
```

Then add to your config:

```vim
" init.vim
set termguicolors
colorscheme adwaita-amoled
```

```lua
-- init.lua
vim.opt.termguicolors = true
vim.cmd('colorscheme adwaita-amoled')
```

If you use vim-airline, copy the airline theme as well:

```bash
mkdir -p ~/.config/nvim/autoload/airline/themes
cp ~/.themes/Adwaita-AMOLED/extra/nvim/autoload/airline/themes/adwaita_amoled.vim ~/.config/nvim/autoload/airline/themes/
```

```vim
let g:airline_theme = 'adwaita_amoled'
```

---

## Building and testing

Install GLib's resource compiler and `rsync` before using `--install`:

```bash
# Debian / Ubuntu
sudo apt install libglib2.0-dev rsync
# Arch / Artix
sudo pacman -S glib2 rsync
```

```bash
./build.sh
./build.sh --install
```

`--install` copies the theme to `~/.local/share/themes/Adwaita-AMOLED` and
replaces `~/.config/gtk-4.0/gtk.css` with the source overrides. Back up an
existing custom override first. After editing `src/`, rebuild and commit the
updated `gtk.gresource` bundles together with their source changes.
The installer honors `XDG_DATA_HOME` and `XDG_CONFIG_HOME` when they are set.

The GNOME Shell CSS is also included precompiled. After changing its Sass
palette, rebuild it separately with `./gnome-shell/build.sh` (requires `sassc`).

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
| Foreground | `#ffffff` | Primary text |
| Dim | `#a0a0a0` | Readable secondary text |

White on the filled GTK accent has approximately 4.89:1 contrast. Extras that
use the pale `#8ab4f8` as a text background use black text (9.96:1).
Success surfaces use black text on `#26a269` (approximately 6.45:1).

---

## Structure

```
Adwaita-AMOLED/
├── cinnamon/               Cinnamon shell theme
├── gnome-shell/            GNOME Shell 51 theme, assets and Sass source
├── gtk-2.0/                GTK2 theme (murrine engine)
├── gtk-3.0/                GTK3 theme
├── gtk-4.0/                GTK4 theme
├── metacity-1/             Metacity / Muffin window decorations
├── openbox-3/              Openbox window manager theme
├── extra/
│   ├── alacritty/          Alacritty terminal theme
│   ├── kitty/              Kitty terminal theme
│   ├── libadwaita/         gtk.css + gtk-dark.css → copy to ~/.config/gtk-4.0/
│   ├── logo/               Theme logo
│   ├── nvim/               Neovim colorscheme and airline theme
│   ├── qt5ct/              Qt5 color scheme
│   ├── qt6ct/              Qt6 color scheme
│   ├── rofi/               Rofi launcher theme
│   ├── screenshot/         Preview image
│   ├── wallpaper/          Matching wallpaper
│   └── zsh/                Zsh autosuggestions & syntax highlighting config
└── index.theme
```

---

## Philosophy

Minimal, readable, and actually usable.
No washed-out grays, no invisible states.
