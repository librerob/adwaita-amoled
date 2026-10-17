These checks exercise the native theme consumers and verify that committed
GResource bundles contain the current source. Python 3.11 or newer is required.

Install the tools on Debian/Ubuntu:

```bash
sudo apt install libglib2.0-dev rsync shellcheck zsh kitty neovim vim-airline \
  python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtk-4.0 gir1.2-adw-1 \
  libmetacity3 xvfb xauth bat rofi flatpak xfconf libxfconf-0-3 dbus-x11 gsettings-desktop-schemas librsvg2-bin python3-pyqt5 python3-pyqt6 \
  libgtk2.0-0t64 gtk2-engines-murrine
```

From the repository root:

```bash
shellcheck install.sh build.sh
python3 tests/test_installer.py
python3 tests/test_flatpak_installer.py
python3 tests/test_manual_installation.py
sudo xvfb-run -a python3 tests/test_system_installer.py
xvfb-run -a python3 tests/test_install_consumers.py
zsh -n extra/zsh/.zshrc
python3 tests/test_theme.py
python3 tests/test_readability.py
xvfb-run -a -s '-screen 0 1600x1200x24' python3 tests/test_runtime.py
xvfb-run -a python3 tests/test_consumers.py
```

`test_theme.py` checks the shipping and freshly compiled bundle contents, asset
references, selected-text contrast, Kitty's native parser, clean-shell Zsh
loading with an insecure completion-path fixture and hook preservation, Neovim
highlight loading, and repeatable
installation into temporary XDG directories through `build.sh --install`. It
checks the Bash installer without Python in its PATH.
The installer has separate file-copy, removal and native loading checks below. Contrast checks cover the
success foreground/background pair, Openbox titles and secondary editor text;
Neovim's actual loaded highlights are checked as well.

`test_runtime.py` runs GTK3, GTK4 and libadwaita in separate processes. It parses
the theme and overrides, renders representative widget states, checks the GTK3
slider's actual pixels, exercises 2,000 toggles and click signals per fixture,
and creates/destroys 200 windows per fixture. The Metacity check loads the XML
through libmetacity and renders 504 combinations of window type, frame state,
focus, button state and scale, including titleless menu/border frames.
The libadwaita fixture resolves the success-color pair through GTK and verifies
its contrast. On libadwaita 1.7 or newer it also checks the foreground of a real
`.success.suggested-action` button, which consumes that pair through accent
variables.
Two additional native checks request light and dark schemes, resolve real accent,
success, warning, error and destructive widget text, and check the resulting
colors and contrast on black. They use `gtk-modern.css` on GTK 4.16 or newer,
and the legacy entry point on older GTK versions. The modern entry point is
tested separately from the legacy overrides; it must not be installed on GTK
versions that cannot parse CSS variables.

Set `THEME_TEST_OUTPUT` to an output directory to retain GTK screenshots and
representative Metacity renders. GitHub Actions uploads these images as the
`theme-rendering` and `theme-rendering-modern` artifacts. Its Ubuntu 26.10
container job exercises the modern libadwaita entry point alongside the
Ubuntu 24.04 checks. Missing required native libraries fail the runtime
checks rather than silently skipping them.
Failures are also emitted as GitHub check annotations, with the original test
exit status preserved, so they remain visible without downloading run logs.

The GTK regression tests above use software rendering under X11. They do not establish native
Wayland, Brave, Flatpak, full Cinnamon/Marco session, physical OLED, or GPU-driver
correctness. GTK's older `alpha()` color function keeps the Chromium rules
compatible with GTK4 releases before `color-mix()` support.

## GNOME Shell 51

On Ubuntu 26.10, install the separate Shell test prerequisites:

```bash
sudo apt install gnome-shell gnome-shell-extension-user-theme mutter-51-tests \
  python3-dbusmock python3-dbus sassc pipewire wireplumber
python3 tests/test_shell.py
```

These four checks verify all pinned upstream source/asset hashes, reproduce the
compiled stylesheet, compare its layout and selectors with upstream, and start
a real headless Wayland Shell on isolated D-Bus services. The native case loads
the theme through User Themes, checks native surface colors and style nodes at
1×/2×, cycles quick settings/calendar menus, and captures eight rendered views.
Set `THEME_TEST_OUTPUT` to retain screenshots, the session log and JSON counters.
The fixture uses upstream GNOME service mocks; it does not test real login,
authentication, power management or physical GPU hardware. Missing Shell 51 or
test dependencies fail the check rather than skipping it.

The Shell 51 fixture additionally uses real pointer events on the panel clock,
calendar days, Show Apps, a pinned application icon and quick-settings split buttons. Its upstream calendar
no longer has the Do Not Disturb control present in 46. Interaction
screenshots are saved separately from the original eight views.
When the mock power service does not expose a split button, the fixture inserts
GNOME's actual `QuickMenuToggle` widget into the menu and records that fact.

### GNOME Shell 46

On Ubuntu 24.04, use its separate upstream-matched variant and native session:

```bash
sudo apt install gnome-shell gnome-shell-extensions mutter-14-tests \
  python3-dbusmock python3-dbus sassc pipewire wireplumber librsvg2-common
python3 tests/test_shell46.py
```

These checks verify all 52 pinned GNOME 46.10 source/assets, reproduce its CSS,
retain upstream geometry, and install the automatically selected 46 stylesheet
into an isolated home. A test-only extension drives a real headless Wayland
session with virtual pointer motion/clicks. Assertions cover panel clock hover/click,
calendar hover and selection, Do Not Disturb SVG states, Show Apps and a pinned
application's hover, and non-overlapping split
button geometry. Set `THEME_TEST_OUTPUT` to retain screenshots, logs and JSON.
As a negative control, setting `THEME_TEST_SHELL_VERSION=51` deliberately installs
the incompatible stylesheet; the GNOME 46 interaction test must fail.
The same service-mock/hardware/login boundaries apply as for the 51 fixture.

## Color readability coverage

`xvfb-run -a python3 tests/test_borders.py` checks native GTK3/GTK4 frame pixels
for ordinary package-card buttons, toolbar buttons, header/location separators
and text fields in normal, hover and backdrop states. Decorative edges stay
subtle while field boundaries retain at least 3:1 contrast; GTK3 keyboard focus
is checked separately. `THEME_TEST_OUTPUT` retains JSON measurements and a GTK3
gallery matching Software Manager's basic Gtk.Button card structure. The fixture
does not run Software Manager's complete catalog/backend. `border_native.py`'s
`--record-only` mode records the previous theme for before/after comparison.

`test_readability.py` checks terminal text, faint compositing, selected matches,
bat syntax across supported backgrounds, Qt active/inactive roles and alpha
placeholders, optional Qt scrollbar handles, Openbox labels/buttons, Zsh ANSI
completion pairs, and the standalone accent on six dark surfaces.

The native Neovim check resolves 736 ordinary/structural highlight pairs on
normal, float, cursor-line and selection backgrounds. It also loads the real
vim-airline plugin and checks 70 true-color/256-color mode pairs. Set
`THEME_AIRLINE_RUNTIME` when that plugin is installed outside `/usr/share/vim-airline`.

Five additional `test_runtime.py` cases use GTK's native Cairo background
renderer and actual label foregrounds across eleven states, including flat semantic actions and GTK3 tasklist/launcher roles.
They check GTK3 plus plain GTK4/libadwaita requesting light and dark modes.
Their 1,199 state samples retain 109 disabled measurements separately; enabled text
must meet 4.5:1. Background gradients are sampled across the control interior. GTK3 style/widget
opacity and GTK4 native snapshot text/opacity nodes are included.

`test_consumers.py` checks native Qt5/Qt6 QPalette colors and renders a Fusion
widget gallery, resolves GTK2 style colors and paints Murrine button/scrollbar/scale states,
builds/uses bat's actual theme cache, parses the Rofi theme, and renders every
SVG through librsvg. GitHub Actions uploads Qt images and GTK2 measurements in
`extra-consumer-rendering`.

The Shell automation additionally checks 936 control/glyph pairs across
all nine system accents and compound hover/focus/active states, including Looking
Glass switches. It separately checks 162 scrollbar graphic pairs and placeholder
text with three interface font sizes. It connects its
virtual monitor after automation initialization, following upstream's
`tests/shell/headlessStart.js`, to avoid missing the startup-complete signal.

The Cinnamon integration fixture runs as a separate CI job and requires an isolated test
container/VM with Cinnamon 6.6 and its session packages:

```bash
xvfb-run -a -s '-screen 0 1600x1200x24 +extension GLX +render -noreset' \
  dbus-run-session -- python3 tests/cinnamon_colors.py . /tmp/amoled-cinnamon-colors
```

It uses temporary user settings, checks 125 representative text/state/overlay pairs,
and evaluates style nodes at the session's native scale. A running system D-Bus service is required;
real login/power/network behavior is not established by this fixture.
See [the color audit](../COLOR_READABILITY.md) for measured improvements,
intentional exceptions and limits. Passing these tests does not establish full
WCAG conformance or cover arbitrary application-provided colors.

Five further native runtime cases cover 241 GTK3 inherited/compound/context
pairs and 33 selected-row descendant pairs for each of GTK3, plain GTK4 and
light/dark libadwaita. The GTK3 contexts include calendar adjacent-month dates,
menu accelerators, selection-header glyphs, checked/backdrop content controls,
focus outlines, named semantic colors, and print-preview ink against paper and
ruler canvas. Ordinary enabled text must meet 4.5:1, and identifying graphics
and focus outlines 3:1. Selected-row tests use actual widgets; some GTK3
compound checks deliberately construct CSS nodes to exercise specific selectors.
See [the repository-wide follow-up](../COLOR_COMPLETENESS.md) for the
reproduced failures, full inventory scope and limits.


## Direct Bash installer

`test_installer.py` runs the actual Bash script with isolated HOME/XDG roots.
It checks fresh copies, overwrite updates despite changed files/modes and old
state, GTK4 links for both entry points, no-Python PATH installation, absent
state/backups, dry runs, duplicate legacy copies, explicit destinations/profiles,
selected extras without changes to personal configs, Shell 46/51 selection,
unsupported options and reproducible runtime-only archives. The archive contains
no Python installer or source/build dependency.

`test_install_consumers.py` runs the script, then checks automatically loaded
GTK4/libadwaita user CSS in both light/dark modes on older/current GTK. Its extras
case explicitly selects the copied files in real Kitty, bat, Neovim, Rofi and
Zsh, checks Qt palette bytes/Alacritty TOML, and verifies app settings remain
untouched by installation and removal. It does not claim the script activates
extras automatically.

`test_install_settings.py` checks actual GSettings selection for isolated
GNOME/Budgie, Cinnamon and MATE users, and xfconf selection in a private D-Bus
session for Xfce. Removal intentionally leaves preferences selected. A local
Shell schema case uses real GSettings with simulated Shell/extension commands;
the separate native Shell sessions test actual User Themes loading.

`test_system_installer.py` runs as root and stages the shared installation in a
temporary parent. It checks owner/public read/traversal permissions, resource
bytes, repeated replacement, removal and refusal of mixed personal/shared scope.
`test_flatpak_installer.py` checks per-app command arguments and link paths using
a Flatpak command fixture; actual sandbox loading is covered separately below.
`test_manual_installation.py` executes the documented copy commands and both
GTK4 entry points; its optional manual backup examples remain separate from the
Bash installer, which creates no backups.

The `flatpak-sandbox` CI job builds a tiny GTK4/libadwaita application and a minimal
runtime from the runner's installed libraries, signs both with a temporary GPG
key, installs them from a local verified repository, and runs the actual app in
Flatpak. It checks the unmodified background first, black background/pale accent
in light and dark modes after installation, explicit runtime-specific stylesheet
selection, per-app removal and retention of unrelated later permissions. It downloads no
third-party app/runtime and disables no signature checks. Required tools:

```bash
sudo apt install flatpak gnupg pax-utils gcc pkg-config libgtk-4-dev libadwaita-1-dev \
  fonts-dejavu-core gsettings-desktop-schemas xvfb xauth dbus-x11
sudo dbus-run-session -- xvfb-run -a python3 tests/test_flatpak_runtime.py
```

A restricted local environment can run `--prepare-only` to check signed export,
installation, explicit runtime selection, configuration/update/removal without a sandbox launch.
That mode is explicitly rejected in CI. A successful preparation run does not
establish rendered Flatpak coverage; the full CI case must also pass. These
fixtures do not cover every Flatpak runtime, application, device or GUI session.
