#!/usr/bin/env python3
"""Build a reproducible installer-enabled runtime archive from this checkout."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

import install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, help="Archive filename outside the checkout"
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(install.ROOT):
        parser.error("write the archive outside the checkout")
    files = []
    for path in sorted(install.ROOT.rglob("*")):
        name = path.relative_to(install.ROOT)
        if name.parts[0] not in install.DIRS and str(name) not in install.FILES:
            continue
        if "__pycache__" in name.parts or not path.is_file():
            continue
        if path.is_symlink():
            parser.error(f"unexpected source link: {name}")
        files.append(
            (name, path.read_bytes(), 0o755 if path.stat().st_mode & 0o111 else 0o644)
        )
    for required in [
        "install.sh",
        "tools/install.py",
        "tools/flatpak_support.py",
        "tools/legacy-gtk4.json",
        "INSTALLING.md",
        "gtk-3.0/gtk.gresource",
        "gtk-4.0/gtk.gresource",
    ]:
        if not any(str(name) == required for name, _, _ in files):
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
            info = tarfile.TarInfo(str(Path(install.THEME) / name))
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
