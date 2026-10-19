#!/usr/bin/env python3
"""Generate the folder-only Adwaita derivative from pinned SVGs and our palette."""
import argparse
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import generate_palette as palette

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = Path("icons/upstream/51.0")
OUTPUT = Path("extra/icons/Adwaita-AMOLED")
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ALIASES = {
    "folder-open": "folder",
    "inode-directory": "folder",
    "folder-downloads": "folder-download",
    "folder-bookmarks": "user-bookmarks",
}


def mix(a, b, amount):
    channels = []
    for index in (1, 3, 5):
        first = int(a[index:index + 2], 16)
        second = int(b[index:index + 2], 16)
        channels.append(f"{round(first * (1 - amount) + second * amount):02x}")
    return "#" + "".join(channels)


def shades(colors):
    # Folder emblems share this upstream shade with the back panel. The pressed
    # fill gives their thin outlines at least 3:1 against every preset's face.
    return {
        "#438de6": colors["accent_fill_pressed"],
        "#a4caee": colors["accent_text"],
        "#62a0ea": mix(colors["accent_fill"], colors["accent_text"], 0.45),
        "#afd4ff": colors["accent_text_hover"],
        "#c0d5ea": mix(colors["accent_text"], "#ffffff", 0.2),
    }


def files(root=ROOT, colors=None, accent="blue"):
    colors = colors or palette.preset_colors(root, "blue")
    upstream = root / UPSTREAM
    pinned = set()
    for line in (upstream / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if (name in pinned
                or not re.fullmatch(r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*", name)
                or ".." in Path(name).parts):
            raise ValueError("invalid upstream manifest path: " + name)
        pinned.add(name)
        if hashlib.sha256((upstream / name).read_bytes()).hexdigest() != digest:
            raise ValueError("upstream artwork changed: " + name)
    actual = {
        str(p.relative_to(upstream)) for p in upstream.rglob("*")
        if p.is_file() and p.name != "SHA256SUMS"
    }
    if pinned != actual:
        raise ValueError("unlisted or missing upstream artwork")
    mapping = shades(colors)

    def recolor(text):
        return re.sub(r"#[0-9a-fA-F]{6}\b", lambda m: mapping.get(m[0].lower(), m[0]), text)

    result = {}
    notice = '<!-- Adwaita-AMOLED: folder colors modified 2026-10-19. Original artwork: GNOME Project. GNU LGPL v3; see COPYING and README.md. -->\n'
    for source in sorted((upstream / "Adwaita/scalable/places").glob("*.svg")):
        text = source.read_text()
        result["scalable/places/" + source.name] = (notice + recolor(text)).encode()
        small = ET.fromstring(text)
        small.set("width", "16")
        small.set("height", "16")
        result["16x16/places/" + source.name] = (notice + recolor(ET.tostring(small, encoding="unicode"))).encode()
    for alias, original in ALIASES.items():
        for directory in ("scalable/places", "16x16/places"):
            result[f"{directory}/{alias}.svg"] = result[f"{directory}/{original}.svg"]
    result["index.theme"] = b"""[Icon Theme]
Name=Adwaita-AMOLED
Comment=Palette-matched Adwaita folders; other icons inherit Adwaita
Inherits=Adwaita,hicolor
Directories=16x16/places,scalable/places

[16x16/places]
Size=16
Context=Places
Type=Fixed

[scalable/places]
Size=128
MinSize=24
MaxSize=512
Context=Places
Type=Scalable
"""
    for name in ("COPYING", "COPYING_LGPL", "COPYING_CCBYSA3"):
        result[name] = (upstream / name).read_bytes()
    # LGPL v3 incorporates GPL v3; keep both texts with standalone icon installs.
    result["COPYING_GPL"] = (root / "LICENSE").read_bytes()
    result["README.md"] = (root / "icons/UPSTREAM.md").read_bytes()
    result["accent-name"] = (accent + "\n").encode()
    names = sorted([*result, "runtime-files.txt", "SHA256SUMS"])
    result["runtime-files.txt"] = ("\n".join(names) + "\n").encode()
    result["SHA256SUMS"] = "".join(
        hashlib.sha256(data).hexdigest() + "  " + name + "\n"
        for name, data in sorted(result.items())
    ).encode()
    return {str(OUTPUT / name): data for name, data in result.items()}


def generate(root=ROOT, colors=None, check=False, accent="blue"):
    outputs = files(root, colors, accent)
    existing = {
        str(p.relative_to(root)) for p in (root / OUTPUT).rglob("*") if p.is_file()
    }
    if existing - outputs.keys():
        raise ValueError("unexpected icon files; inspect before regenerating")
    changed = [
        name for name, data in outputs.items()
        if not (root / name).is_file() or (root / name).read_bytes() != data
    ]
    if check and changed:
        raise ValueError("stale icon outputs: " + ", ".join(changed))
    if not check:
        for name in changed:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(outputs[name])
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        print(f"Folder icon generation: {len(generate(check=args.check))} changed files")
    except (OSError, ValueError, StopIteration) as error:
        parser.exit(1, f"Icon generation failed: {error}\n")
