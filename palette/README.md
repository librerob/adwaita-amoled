# Shared palette generation

`colors.json` holds 46 shared color values for the default blue theme.
`accents.json` supplies complete `accent_*` overrides for yellow, gold, purple,
green, red, orange and pink. Neutral and semantic roles retain the base values. `templates/` supplies the 76 generated
source, configuration and SVG files that use them. Templates have the output's
repository path plus `.in`; for example,
`templates/src/gtk-3.0/gtk-main.css.in` generates `src/gtk-3.0/gtk-main.css`.

For generated files, edit the template for layout or toolkit-specific styling;
edit `colors.json` for a shared color. Do not edit the generated output directly.
Files without a matching template remain maintained in their original location.
The expanded role mapping preserves default blue rendered files byte-for-byte.

From the repository root, using Python 3.11 or newer:

```bash
python3 tools/generate_palette.py
python3 tools/generate_palette.py --check
./build.sh
./gnome-shell/build.sh
./gnome-shell/build.sh --shell-version 46
python3 tools/build_accents.py
python3 tools/build_accents.py --check
```

GTK rebuilding needs GLib's resource compiler; Shell rebuilding needs `sassc`.
Commit palette/template changes, generated files and rebuilt GTK/Shell outputs
together. The accent builder compiles all seven presets in temporary directories
and stores only files differing from blue under `accents/<name>/`, with per-color
and distribution SHA-256 manifests. `--check` rebuilds and compares without
writing. Unexpected existing overlay files require inspection rather than silent
deletion. Blue outputs and pinned upstream sources remain untouched.

CI checks generation and native/source/bundle tests. Changing
a color still requires contrast and native rendering review; generation does
not establish that a new palette is readable.

## Token syntax and scope

- `{{accent_text}}` emits `#8ab4f8`.
- `{{accent_text.hex}}` emits `8ab4f8`; Qt uses `#ff{{accent_text.hex}}`
  to preserve its explicit alpha byte.
- `.upper` and `.hex_upper` preserve uppercase formats where needed.
- `.r`, `.g` and `.b` emit decimal channels, preserving existing `rgba()` spacing
  and alpha values in templates.

Shared values include black/white primitives (`background` and `foreground`),
surface levels, borders, pale-blue text/focus, darker blue fills, status colors
and common syntax colors. Black/white also appear in inverse labels and glyphs;
the tokens are shared values, not a guarantee that every use has the same role.
Split a token into separate roles before changing one use independently.

Accent roles include hover/pressed/disabled shades, tinted selection surfaces,
legacy gradients and task indicators. Independent syntax colors, indexed terminal
colors, toolkit-specific neutrals and alpha values remain separate. This is not
a global replacement of every hexadecimal value. Pinned upstream Sass and
original artwork are not rewritten; Shell 46 preset controls use derived SVG
copies. The base generator writes neither GTK resources nor
compiled Shell CSS; the accent builder invokes the normal build tools for those.

GNOME Shell 51's new presets resolve native accent expressions by property:
light text/focus, dark fills and white labels. Its default blue build retains
GNOME Settings' accent behavior. Selectors and geometry stay unchanged.

Presets must define every base `accent_*` role and cannot override semantic or
neutral roles. Unknown tokens, malformed colors and duplicate JSON keys fail.
`--check` reports
missing/stale generated files without writing them. Templates are validated
before any output is changed. The generator uses only Python's standard library.

Templates and this tool are development inputs. They are excluded from
`runtime-files.txt`, so users need no Python and download no palette sources.

See [accent choices, measured contrast and limitations](../ACCENT_COLORS.md).
