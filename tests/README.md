These checks exercise the native theme consumers and verify that committed
GResource bundles contain the current source. Python 3.11 or newer is required.

Install the tools on Debian/Ubuntu:

```bash
sudo apt install libglib2.0-dev rsync shellcheck zsh kitty neovim \
  python3-gi gir1.2-gtk-3.0 gir1.2-gtk-4.0 gir1.2-adw-1 \
  libmetacity3 xvfb xauth
```

From the repository root:

```bash
shellcheck build.sh
zsh -n extra/zsh/.zshrc
python3 tests/test_theme.py
xvfb-run -a -s '-screen 0 1600x1200x24' python3 tests/test_runtime.py
```

`test_theme.py` checks the shipping and freshly compiled bundle contents, asset
references, selected-text contrast, Kitty's native parser, clean-shell Zsh
loading with an insecure completion-path fixture and hook preservation, Neovim
highlight loading, and repeatable
installation into temporary XDG directories. It also checks that a missing
`rsync` fails before rebuilding or installing anything.

`test_runtime.py` runs GTK3, GTK4 and libadwaita in separate processes. It parses
the theme and overrides, renders representative widget states, checks the GTK3
slider's actual pixels, exercises 2,000 toggles and click signals per fixture,
and creates/destroys 200 windows per fixture. The Metacity check loads the XML
through libmetacity and renders 504 combinations of window type, frame state,
focus, button state and scale, including titleless menu/border frames.

Set `THEME_TEST_OUTPUT` to an output directory to retain GTK screenshots and
representative Metacity renders. GitHub Actions uploads these images as the
`theme-rendering` artifact. Missing required native libraries fail the runtime
checks rather than silently skipping them.
Failures are also emitted as GitHub check annotations, with the original test
exit status preserved, so they remain visible without downloading run logs.

These tests use software rendering under X11. They do not establish native
Wayland, Brave, Flatpak, full Cinnamon/Marco session, physical OLED, or GPU-driver
correctness. GTK's older `alpha()` color function keeps the Chromium rules
compatible with GTK4 releases before `color-mix()` support.
