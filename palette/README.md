# Shared palette generation

`colors.json` holds 24 shared color values. `templates/` supplies the 76 generated
source, configuration and SVG files that use them. Templates have the output's
repository path plus `.in`; for example,
`templates/src/gtk-3.0/gtk-main.css.in` generates `src/gtk-3.0/gtk-main.css`.

For generated files, edit the template for layout or toolkit-specific styling;
edit `colors.json` for a shared color. Do not edit the generated output directly.
Files without a matching template remain maintained in their original location.
The initial generated outputs match v1.4.1 byte-for-byte. This change does not
alter any color, widget geometry, compiled resource or runtime asset.

From the repository root, using Python 3.11 or newer:

```bash
python3 tools/generate_palette.py
python3 tools/generate_palette.py --check
./build.sh
./gnome-shell/build.sh
./gnome-shell/build.sh --shell-version 46
```

GTK rebuilding needs GLib's resource compiler; Shell rebuilding needs `sassc`.
Commit palette/template changes, generated files and rebuilt GTK/Shell outputs
together. CI checks generation and existing native/source/bundle tests. Changing
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

Toolkit-specific state shades, alpha values, gradients, independent syntax
colors, indexed terminal colors and upstream Shell accent behavior remain in
their templates or original sources. Pinned upstream Sass and Shell artwork
are not rewritten. The generator writes neither GTK resources nor compiled
Shell CSS; the normal build tools remain responsible for those outputs.

Unknown tokens, malformed colors and duplicate JSON keys fail. `--check` reports
missing/stale generated files without writing them. Templates are validated
before any output is changed. The generator uses only Python's standard library.

Templates and this tool are development inputs. They are excluded from
`runtime-files.txt`, so users need no Python and download no palette sources.
