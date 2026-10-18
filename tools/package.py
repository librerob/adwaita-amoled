#!/usr/bin/env python3
"""Build a reproducible installer-enabled runtime archive from this checkout."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
THEME = "Adwaita-AMOLED"


def runtime_paths(root):
    """The Bash installer consumes this same explicit file list."""
    names = (root / "runtime-files.txt").read_text().splitlines()
    if not names or len(set(names)) != len(names):
        raise ValueError("empty or duplicate runtime file list")
    for name in names:
        path = Path(name)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*", name) or any(
            part in (".", "..") for part in name.split("/")
        ):
            raise ValueError(f"invalid runtime path: {name}")
        source = root / path
        if not source.is_file() or any(
            p.is_symlink() for p in (source, *source.parents) if p != root
        ):
            raise ValueError(f"missing or linked runtime file: {name}")
    if "runtime-files.txt" not in names:
        raise ValueError("runtime list must include runtime-files.txt")
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, help="Archive filename outside the checkout"
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        parser.error("write the archive outside the checkout")
    files = []
    try:
        names = runtime_paths(ROOT)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for name in sorted(names):
        path = ROOT / name
        files.append(
            (
                Path(name),
                path.read_bytes(),
                0o755 if path.stat().st_mode & 0o111 else 0o644,
            )
        )
    for required in [
        "install.sh",
        "INSTALLING.md",
        "index.theme",
        "gtk-2.0/gtkrc",
        "gtk-3.0/gtk.css",
        "gtk-3.0/gtk.gresource",
        "gtk-4.0/gtk.css",
        "gtk-4.0/gtk.gresource",
        "cinnamon/cinnamon.css",
        "metacity-1/metacity-theme-3.xml",
        "openbox-3/themerc",
        "gnome-shell/gnome-shell-46.css",
        "gnome-shell/gnome-shell-51.css",
        "extra/libadwaita/gtk.css",
        "extra/libadwaita/gtk-modern.css",
        "extra/libadwaita/gtk-dark.css",
        "extra/libadwaita/libadwaita-tweaks.css",
    ]:
        if not any(str(name) == required and data for name, data, _ in files):
            parser.error("incomplete runtime: " + required)
    manifest = "".join(
        hashlib.sha256(data).hexdigest() + "  " + str(name) + "\n"
        for name, data, _ in files
    ).encode()
    files.append((Path("ARCHIVE_CONTENTS.sha256"), manifest, 0o644))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Fixed timestamps, IDs, modes and gzip filename make repeat builds identical.
    with output.open("wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, mtime=0
    ) as compressed, tarfile.open(
        fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
    ) as archive:
        for name, data, mode in files:
            info = tarfile.TarInfo(str(Path(THEME) / name))
            info.size, info.mode, info.mtime = len(data), mode, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(
        checksum + "  " + output.name + "\n"
    )
    print(
        f"{len(files)} files; {output.stat().st_size} bytes; SHA-256 {checksum}\n{output}"
    )


if __name__ == "__main__":
    main()
