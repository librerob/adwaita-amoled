#!/usr/bin/env python3
"""Create the README's folder showcase from the committed icon presets."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import generate_palette as palette

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("extra/readme/folder-presets.svg")
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
PRESETS = ("blue", "yellow", "gold", "purple", "green", "red", "orange", "pink")
SPECIAL = ("user-home", "folder-documents", "folder-download", "folder-music",
           "folder-pictures", "folder-videos")


def element(parent, tag, **attributes):
    return ET.SubElement(parent, f"{{{SVG}}}{tag}", attributes)


def artwork(root, accent, name, prefix, x, y, size):
    relative = Path("extra/icons/Adwaita-AMOLED/scalable/places") / (name + ".svg")
    overlay = root / "accents" / accent / relative
    path = overlay if accent != "blue" and overlay.is_file() else root / relative
    svg = ET.fromstring(path.read_bytes())
    # SVG IDs are document-wide: each gradient needs its own name in the chart.
    ids = {e.attrib["id"]: prefix + e.attrib["id"] for e in svg.iter() if "id" in e.attrib}
    for node in svg.iter():
        for key, value in list(node.attrib.items()):
            if key == "id":
                node.set(key, ids[value])
            else:
                for old, new in ids.items():
                    value = value.replace(f"url(#{old})", f"url(#{new})")
                    if value == "#" + old:
                        value = "#" + new
                node.set(key, value)
    svg.attrib.update(x=str(x), y=str(y), width=str(size), height=str(size))
    return svg


def render(root=ROOT):
    base = palette.preset_colors(root, "blue")
    svg = ET.Element(f"{{{SVG}}}svg", {
        "width": "960", "height": "440", "viewBox": "0 0 960 440",
        "role": "img", "aria-labelledby": "title description",
    })
    element(svg, "title", id="title").text = "Adwaita-AMOLED folder icon presets"
    element(svg, "desc", id="description").text = (
        "Eight real icon presets: blue (default), yellow, gold, purple, green, red, orange and pink. "
        "Each card shows the folder, Home, Documents, Downloads, Music, Pictures and Videos artwork."
    )
    svg.append(ET.Comment("Artwork: GNOME Project, Adwaita Icon Theme 51.0; palette derivatives under GNU LGPL v3. See icons/UPSTREAM.md and the included license texts."))
    element(svg, "rect", width="960", height="440", rx="18", fill=base["background"])
    for index, accent in enumerate(PRESETS):
        colors = palette.preset_colors(root, accent)
        card = element(svg, "g", transform=f"translate({18 + (index % 4) * 234} {16 + (index // 4) * 212})",
                       **{"font-family": "DejaVu Sans, sans-serif"})
        element(card, "rect", width="220", height="196", rx="14",
                fill=base["surface"], stroke=base["decorative_border"])
        element(card, "text", x="16", y="31", fill=colors["accent_text"],
                **{"font-size": "18", "font-weight": "600"}).text = accent.capitalize()
        if accent == "blue":
            element(card, "rect", x="145", y="14", width="59", height="22", rx="11", fill=base["pressed"])
            element(card, "text", x="174.5", y="29", fill=base["secondary_text"],
                    **{"font-size": "10", "text-anchor": "middle"}).text = "DEFAULT"
        card.append(artwork(root, accent, "folder", f"{accent}-folder-", 62, 40, 96))
        for position, name in enumerate(SPECIAL):
            card.append(artwork(root, accent, name, f"{accent}-{name}-", 15 + position * 33, 155, 24))
    ET.indent(svg, space="  ")
    return ET.tostring(svg, encoding="unicode") + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / OUTPUT
    content = render()
    if args.check:
        if not target.is_file() or target.read_text() != content:
            parser.exit(1, "Folder showcase is stale; run python3 tools/showcase_icons.py.\n")
        print("Folder showcase matches the committed presets.")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        print(OUTPUT)
