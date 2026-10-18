"""Measure the actual librsvg paint of preset checkbox focus rings."""

import json
from pathlib import Path
import subprocess
import sys

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf
from test_theme import contrast

root, output = map(Path, sys.argv[1:3])
output.mkdir(parents=True, exist_ok=True)
pairs = []
for name in ("checkbox-off-focused.svg", "checkbox-focused.svg"):
    for background in ("#000000", "#141414", "#252525"):
        image = output / (name + "-" + background[1:] + ".png")
        subprocess.run(
            [
                "rsvg-convert",
                "--background-color",
                background,
                "--width",
                "240",
                "--height",
                "240",
                "--output",
                str(image),
                str(root / "gnome-shell/assets/46" / name),
            ],
            check=True,
        )
        pixels = GdkPixbuf.Pixbuf.new_from_file(str(image))
        # The straight top edge of both 24px SVG rings, away from rounded
        # corners and inner control paint; 10x scaling avoids edge antialiasing.
        offset = pixels.get_rowstride() * 5 + pixels.get_n_channels() * 120
        color = "#" + pixels.get_pixels()[offset : offset + 3].hex()
        pairs.append(
            {
                "asset": name,
                "background": background,
                "paint": color,
                "contrast": contrast(color, background),
            }
        )
(output / "focus-rings.json").write_text(json.dumps(pairs, indent=2) + "\n")
assert all(pair["contrast"] >= 3 for pair in pairs), pairs
print(
    json.dumps(
        {
            "focus_pairs": len(pairs),
            "minimum_contrast": min(pair["contrast"] for pair in pairs),
        }
    )
)
