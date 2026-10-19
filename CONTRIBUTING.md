# Development

Use a Git checkout or GitHub's source archive for development. The smaller
installer-enabled release archive contains prebuilt runtime files, not the
palette templates or GTK/Shell build sources.

Edit [palette/colors.json](palette/colors.json) for shared base colors and
[palette/accents.json](palette/accents.json) for preset accent roles. For layout
or toolkit-specific rules in generated files, edit their matching
[palette template](palette/README.md). Then regenerate:

```bash
python3 tools/generate_palette.py
python3 tools/generate_palette.py --check
python3 tools/generate_icons.py
python3 tools/generate_icons.py --check
```

Python 3.11+ is a development dependency only. Generated files are committed, so
users still install with Bash alone. Toolkit-specific colors and upstream Shell
sources retain their own definitions; this is not a global recoloring command.

Folder icon derivatives use the same accent roles; see
[pinned artwork and licensing](icons/UPSTREAM.md). Regenerate icons before
building accent overlays. Original upstream files and their hashes stay unchanged.

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

`--install` builds the GTK bundles, then runs the Bash installer. Additional
installer options can follow `--install`, for example `./build.sh --install -l`.
No Python is required to build GTK resources or install the theme.
After editing `src/`, rebuild and commit the updated `gtk.gresource` bundles
together with their source changes. If a corresponding palette template exists,
edit that template rather than the generated `src/` file.

The GNOME Shell CSS is also included precompiled. After changing its Sass
palette, regenerate the shared files and rebuild **both** variants (requires
`sassc` and Python 3.11+):

```bash
./gnome-shell/build.sh
./gnome-shell/build.sh --shell-version 46
```

Then rebuild/check the seven precompiled accent overlays:

```bash
python3 tools/build_accents.py
python3 tools/build_accents.py --check
```

Preset definitions are in [palette/accents.json](palette/accents.json). The build
runs in temporary directories and leaves the default blue outputs unchanged.

Build an installer-enabled runtime archive (without source GTK files or tests):

```bash
python3 tools/package.py /tmp/Adwaita-AMOLED-installer-preview.tar.gz
```

The archive includes `runtime-files.txt` and per-file checksums; a separate SHA-256
file is written beside it. Update the runtime list when adding a required asset
or app extra. This creates local files and does not publish a GitHub release.

The repository's regression checks and their prerequisites are documented in
[tests/README.md](tests/README.md). GitHub Actions runs them on pull requests.
