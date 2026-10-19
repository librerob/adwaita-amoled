# Folder artwork provenance

Source: https://gitlab.gnome.org/GNOME/adwaita-icon-theme
Release: 51.0
Commit: `70ecd52fbe844304ed4f845a04a1757fa6284884`
Mirror used: https://github.com/GNOME/adwaita-icon-theme

Original folder SVG exports and license notices are retained
unchanged under `upstream/51.0/`; SHA256SUMS pins every imported file.
Generated derivatives live under `extra/icons/Adwaita-AMOLED` and the existing
accent overlays. Attribution: GNOME Project (https://www.gnome.org).
These icon derivatives are distributed under GNU LGPL v3; upstream also
offers CC-BY-SA-3.0-US. License texts accompany the installed icon theme.
COPYING_GPL adds the repository's GPL v3 text, incorporated by LGPL v3.

Modified 2026-10-19: only the five blue folder colors are mapped to palette-derived shades. Shapes,
neutral hardware details and emblems are preserved. Symbolic icons are inherited.
Folder faces use accent_text; backs and emblem strokes use accent_fill_pressed,
giving the emblems at least 3:1 contrast against each preset's folder face.
The existing hover color and two deterministic blends preserve edge depth.
Small SVGs use the same exported artwork at 16px, avoiding blue inherited PNGs.
Home, Desktop and bookmark folders are included under their user-* icon names.
Folder-open, folder-downloads, folder-bookmarks and inode-directory aliases
reuse the corresponding folder artwork.

Run `python3 tools/generate_icons.py` after palette changes and before
`python3 tools/build_accents.py`. Generation uses Python standard-library XML tools; installation needs only the
existing Bash tools.
