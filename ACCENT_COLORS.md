# Accent presets

Blue remains the default. Yellow, gold, purple, green, red, orange and pink are
optional presets selected in `./install.sh` → **Accent color**, or with
`./install.sh --accent purple`. Every preset keeps the same black backgrounds,
surface hierarchy, theme name and widget geometry.

## Text and fill are different roles

A single accent cannot provide both light text on black and a background for
white button labels. The presets use separate tones for standalone text/focus
and filled controls. Hover and pressed fills become darker so that white labels
retain contrast. Existing pale Qt/editor selections use black labels; their
light background follows the selected accent.

The table gives defined sRGB contrast. "Raised" means the brightest tested
neutral surface `#252525`. Button labels are white.

| Preset | Text/focus | Text on black | Text on raised | Filled button | White on fill | White on hover | White on pressed |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| Blue (unchanged) | `#8ab4f8` | 9.96:1 | 7.27:1 | `#2d6be0` | 4.89:1 | 5.62:1 | 6.50:1 |
| Yellow | `#d2cf89` | 13.03:1 | 9.51:1 | `#7b7505` | 4.78:1 | 5.13:1 | 5.68:1 |
| Gold | `#edc76f` | 13.00:1 | 9.49:1 | `#956c0b` | 4.74:1 | 5.13:1 | 5.63:1 |
| Purple | `#dcc1ef` | 12.92:1 | 9.43:1 | `#9a4fd0` | 4.77:1 | 5.14:1 | 5.65:1 |
| Green | `#85dea3` | 12.97:1 | 9.47:1 | `#238443` | 4.72:1 | 5.16:1 | 5.65:1 |
| Red | `#f7bebe` | 13.06:1 | 9.54:1 | `#d43737` | 4.77:1 | 5.11:1 | 5.68:1 |
| Orange | `#f3c29e` | 13.02:1 | 9.50:1 | `#ba550d` | 4.78:1 | 5.12:1 | 5.70:1 |
| Pink | `#eebed8` | 12.99:1 | 9.48:1 | `#d02f85` | 4.74:1 | 5.11:1 | 5.66:1 |

Yellow and gold buttons are deliberately dark yellow/olive and ochre. Bright
yellow or gold behind white text cannot meet ordinary-text contrast. Their
standalone accent text remains light. This preserves the requested white-label
button design across all choices.

The presets change accent roles, not every color in an application. Error,
warning, success, syntax categories and ANSI terminal colors retain their
meanings. A red preset still needs error icons/messages; a green preset still
needs success indicators. Color alone must not communicate those meanings.
Wallpaper, logos, screenshots and pinned upstream originals remain unchanged.
Preset Shell 46 switches/checkboxes use derived SVG copies with matching colors.
Their checkbox focus rings also use a measured 60% opacity; the inherited 35%
paint was below 3:1 on the AMOLED surfaces.

## Method and guidance

The targets use the W3C relative-luminance formula for opaque sRGB colors:
ordinary text at least **4.5:1**, standalone accent text at least **7:1** on
the tested AMOLED surfaces, and identifying control graphics at least **3:1**.
Disabled controls are reviewed separately; WCAG does not impose ordinary-text
contrast on inactive components.

For each new hue, tones were chosen near relative luminance 0.60 for light
accent text, 0.17 for normal button fills, 0.155 for hover and 0.135 for pressed
fills. The final 8-bit values were measured again. Saturation is reduced for
light accents; yellow text is less saturated to avoid a neon appearance.
Native tests additionally resolve inheritance, alpha composition, gradients,
backdrop states and toolkit-specific state changes; hexadecimal calculations
alone do not establish what a widget actually paints.

References:

- [W3C: Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [W3C: Contrast (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced.html)
- [W3C: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- [W3C maintained guidance source](https://github.com/w3c/wcag/tree/main/understanding)
- [Material tonal palette implementation](https://github.com/material-foundation/material-color-utilities/blob/main/typescript/palettes/tonal_palette.ts)

Material's separation of hue/chroma/tone provides useful context; this theme
does not use Material's algorithm or claim its colors are Material presets.
WCAG ratios are useful engineering targets, not proof of universal readability
or whole-desktop accessibility conformance. No hue is objectively best for every
person, font size, display or lighting condition. These are measured choices,
not a guarantee of perfect OLED behavior or color-vision accessibility.

## Implementation and testing

`palette/colors.json` defines the unchanged base blue palette.
`palette/accents.json` overrides every `accent_*` role for each new preset.
Semantic and neutral roles cannot be overridden there. The 76 shared templates
cover GTK sources, Cinnamon CSS/SVGs, window decorations and application themes.
`tools/build_accents.py` renders and compiles all seven presets in temporary
directories, then stores only files that differ from blue under `accents/`.
Each preset and the complete distribution have SHA-256 manifests. Airline's
256-color fallback uses the nearest fixed xterm-256 color for its accent roles;
semantic mode/status colors and user-defined ANSI slots stay separate.

The Bash installer combines the base runtime with one verified overlay. It
installs no palette sources, compiler or other presets. Rerunning retains the
installed color unless another is chosen. Rerun with the same optional extras
to refresh copied app snippets; existing GTK4/Flatpak links follow the installed
theme. App themes still need selection in their own applications.

Shell 46 uses the theme preset. Shell 51's new presets also use that preset,
independently of GNOME Settings' accent; the default blue Shell 51 build keeps
its existing system-accent behavior. Neither changes GNOME's accent preference.
The build preserves upstream selectors and geometry, and resolves native Shell
accent expressions into separate text/fill colors for the new presets.

Tests cover every new preset's definitions, compiled output reproducibility,
distribution checksums, installation/update/color switching/removal, guided
selection, root-owned shared installation and failed-copy recovery. Native
consumer tests and their prerequisites are documented in [tests/README.md](tests/README.md).
The supported Shell versions remain **46 and 51**. Other Shell major versions,
physical OLED/GPU behavior and arbitrary third-party app/extension styling
remain outside verified coverage.
