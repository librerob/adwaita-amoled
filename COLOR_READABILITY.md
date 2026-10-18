# Color readability audit — 2026-10-16

The optional seven-color presets and their measurements are documented in
[Accent presets](ACCENT_COLORS.md). The blue-theme findings below remain historical.

This records the original v1.2.0 readability work. The subsequent
[repository-wide color follow-up](COLOR_COMPLETENESS.md) documents additional
failures found by broader tests, their fixes and the current coverage.

The readability palette uses pale blue for standalone accent text and focus
indicators, with dark blue fills and white labels for GTK/Cinnamon buttons.
Pure black remains the main background. This audit inventories the 177 files
in the v1.1.0 repository, including SVG paints, source styles, compiled resources,
desktop themes and every supplied application palette. Changes address measured
color pairs and control visibility. They do not establish that every application,
display or user will experience perfect readability.

## Color roles

| Role | Colors | Defined sRGB contrast |
| --- | --- | --- |
| Standalone accent on black | `#8ab4f8` / `#000000` | 9.96:1 |
| Standalone accent on raised surface | `#8ab4f8` / `#141414` | 8.74:1 |
| Standalone accent on brightest tested neutral surface | `#8ab4f8` / `#252525` | 7.27:1 |
| Filled blue control | `#ffffff` / `#2d6be0` | 4.89:1 |
| Pale editor/Qt selection | `#000000` / `#8ab4f8` | 9.96:1 |
| Identifying border on a control | `#808080` / `#262626` | 3.83:1 |

Text hover blue is `#aecbfa`. Secondary editor/terminal text uses `#a0a0a0` or
lighter colors; faint terminal colors are checked after their configured dimming.
Standalone error, warning and success text use lighter semantic colors, while
filled semantic actions keep separately tested foreground/background pairs.
GNOME Shell retains the user's system-selected accent hue and darkens opaque
accent fills by interaction state so white labels remain readable.

White text on pale blue would have only 2.11:1 contrast. These roles must not be
collapsed into one globally substituted blue. Existing pale selections use black
text; dark blue filled buttons retain white labels, as requested by the owner.

## Confirmed problems and changes

- Neovim floating information text previously resolved to `#387af2` on `#111820`
  (4.45:1). Pale blue raises that pair to 8.48:1. Highlight groups, diagnostics,
  completion selections, whitespace, separators and Airline's true-color and
  256-color palettes are checked through the actual plugins.
- Native GTK4 flat suggested text previously measured 2.76:1; error-entry text
  measured 3.26:1. Standalone and filled roles now have explicit matching styles.
  Native libadwaita suggested hover previously measured 4.40:1. GTK3 backdrop
  actions, flat destructive labels and active links also needed separate
  foreground/background handling. Compound backdrop/active states are tested
  separately. GTK3/plain GTK4 progress text and GTK3 backdrop calendar arrows also used overly
  faint foregrounds.
- Qt's inactive placeholder used a translucent gray that composited to about
  3:1 on its dark entry background. It now uses opaque secondary text. Qt links,
  selection foregrounds and optional scrollbar handles have separate roles.
- Terminal faint red/blue/magenta, bright-black text, Kitty tab indicators and
  Zsh completion pairs needed fixes beyond changing the accent. Bold ANSI black
  is distinct from normal black when validating completion selections.
- Cinnamon dialog hover and error text produced 23 failures in 77 representative
  text/state pairs. Those 77 pairs now meet 4.5:1. Unchecked SVG controls and
  scrollbar handles receive visible identifying paints. The workspace add button
  keeps a dark blue fill behind its white plus.
- The initial native GNOME Shell audit found 364 failures in 432 opaque control
  pairs across nine system accents. State-specific darker fills bring all 432
  above 4.5:1; the lowest measured pair is 4.796:1. All 963 upstream layout rules
  and the 50 pinned upstream source/asset files remain checked against upstream.
  Current builds pin all eight theme presets to their measured text/fill roles,
  independent of GNOME Settings. Blue Shell 46 checkbox focus rings now also use
  derived assets; actual SVG paint is checked on three dark surfaces.
- GTK2 scrollbar/scale thumbs now use a visible dark accent. Native Murrine
  painting checks their interiors as well as button labels. Xfce panel-specific
  resets now retain visible keyboard-focus outlines. GTK3 backdrop checkbox and
  radio borders use the identifying-border color.

## Validation

Reproduction commands and required packages are in [tests/README.md](tests/README.md).
The automated suites contain 45 tests: 14 source/install/consumer regressions,
10 color-role checks, 11 native GTK/libadwaita/Metacity checks, six additional
consumer checks and four GNOME Shell checks. The optional Cinnamon integration
fixture is separate.

| Native coverage | What is measured or exercised |
| --- | --- |
| GTK 3.24 / GTK 4.24 / libadwaita 1.10 | 1,067 color/state samples across GTK3 and light/dark GTK4/libadwaita; 97 disabled samples recorded separately; enabled text must reach 4.5:1 |
| GTK3 identifying graphics | 51 native CSS-node checkbox/radio/calendar-arrow pairs across three surfaces, including checked/indeterminate backdrop states; 3:1 minimum |
| Text opacity | GTK3 style/widget opacity and GTK4 native GSK text/opacity nodes; a dim-label assertion prevents silently ignoring opacity |
| GTK backgrounds | Native Cairo background composition and gradient samples across control interiors |
| GTK lifecycle | 600 window lifecycles and 12,000 toggle/click callbacks across three fixtures |
| GTK2 / Murrine | 30 style/state samples, four painted button states and eight painted scrollbar/scale states; identifying interiors exceed 3:1 |
| Qt5 / Qt6 | 16 active/inactive native QPalette pairs per version and rendered Fusion galleries |
| Neovim / Airline | 736 resolved highlight/background pairs; 70 true-color/256-color Airline pairs |
| GNOME Shell 51.0 and built upstream 51.1 | Headless Wayland Shell with User Themes; 432 accent pairs, 6,822 style queries, 40 menu transitions, eight rendered views; 1×/2× style coverage |
| Cinnamon 6.6.9 | Isolated software X11 session; 77 color pairs and 2,421 style queries at the session's native scale |
| Metacity | 504 rendered frame combinations at 1×/2× |
| Assets and extras | All 61 SVGs rendered with librsvg; bat cache/highlighting, native Rofi parsing, native Kitty parsing, Zsh loading and completion preservation |

Ubuntu 24.04 CI additionally checks the older GTK4/libadwaita compatibility
path; Ubuntu 26.10 exercises the modern CSS-variable entry point. Missing native
dependencies fail the corresponding tests rather than being silently skipped.
The GNOME Shell fixture uses upstream-style service mocks and virtual monitors.

## Intentional exceptions and limits

Disabled controls are recorded separately and are not claimed to meet the enabled
text benchmark. Decorative shadows, surface shading, nonessential separators,
Neovim end-of-buffer markers and SVG editor metadata are not text colors. The
two grayscale Cinnamon overview PNGs are retained; their antialiasing/shadows
are not recolored as accent paints. Logos, wallpaper and historical screenshots
are artwork, not live UI palettes, and remain unchanged. Pinned GNOME upstream
colors remain intact in their source directory; adaptations live outside it.

ANSI normal/dim black remains an intentional background-capable color. Programs
can explicitly request black-on-black, arbitrary ANSI color combinations, custom
backgrounds, external icons or their own CSS. Such pairs are not guaranteed by
these checks. Color blindness, focus/navigation behavior, font size/weight and
non-color cues need consideration beyond numerical contrast.

Ratios use WCAG's sRGB relative-luminance calculation. Enabled ordinary text is
checked against 4.5:1, standalone accent text against 7:1 on six specified dark
surfaces, and selected identifying graphics against 3:1. These checks do not
establish complete WCAG conformance. They measure defined/native colors and
opacity, not perceived comfort, text antialiasing or physical panel output.
The Cairo fixtures sample control interiors rather than proving contrast at
every rounded edge or arbitrary application layout.

Physical OLED/GPU behavior, subpixel layouts, PWM, reflections, power use,
panel lifetime, real login/lock/suspend, Flatpak and Brave remain outside this
color audit's verified coverage. It does not establish complete desktop-session
compatibility for every GNOME, Xfce, Cinnamon, MATE or Budgie release.

## References

- [W3C contrast minimum](https://github.com/w3c/wcag/blob/main/understanding/20/contrast-minimum.html)
- [W3C enhanced contrast](https://github.com/w3c/wcag/blob/main/understanding/20/contrast-enhanced.html)
- [W3C non-text contrast](https://github.com/w3c/wcag/blob/main/understanding/21/non-text-contrast.html)
- [W3C use of color](https://github.com/w3c/wcag/blob/main/understanding/20/use-of-color.html)
- [libadwaita 1.10 standalone color roles](https://github.com/GNOME/libadwaita/blob/1.10.0/doc/css-variables.md#standalone-colors)

These official source mirrors informed the role separation and benchmarks.
There is no verified basis here for calling one blue universally best for OLED
readability or for promising a bug-free theme.
