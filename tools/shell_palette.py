#!/usr/bin/env python3
"""Apply shared accent roles to compiled Shell CSS and derived GNOME 46 assets.

Development only. Pinned upstream Sass and SVG files are never rewritten.
"""
import argparse
from pathlib import Path
import re

import generate_palette as palette

CONTROLS = (
    "checkbox-focused.svg", "checkbox-off-focused.svg", "checkbox-off.svg",
    "checkbox.svg", "toggle-off.svg", "toggle-on.svg",
)


def shell46_asset(text, colors):
    """Derive preset controls without modifying the pinned blue SVG originals."""

    def style(match):
        value = match[1]
        role = "accent_text" if "fill:none;" in value else "accent_fill"
        if role == "accent_text" and "stroke:#3584e4;" in value:
            # Inherited 35% focus rings paint below 3:1 on AMOLED. A 60%
            # ring is measured on black and both raised popup surfaces.
            value = re.sub(
                r"stroke-opacity:(?:\.35|\.34999999)(?=;|$)", "stroke-opacity:.6", value
            )
        return 'style="' + value.replace("#3584e4", colors[role]) + '"'

    text = re.sub(r'style="([^"]*)"', style, text)
    for old, role in (
        ("#3081e3", "accent_fill"),
        ("#0b2e52", "accent_disabled"),
        ("#1862af", "accent_fill_pressed"),
    ):
        text = text.replace(old, colors[role])
    return text


def shell_preset(css, colors):
    """Resolve upstream's dynamic accent in every compiled theme preset.

    Preserve selectors, geometry and upstream sources. Text and opaque fills
    have separate contrast roles, including the default blue build.
    """
    lines = []
    for line in css.splitlines(keepends=True):
        if "-st-accent" not in line:
            lines.append(line)
            continue
        match = re.match(r"\s*([\w-]+):", line)
        if not match:
            raise ValueError("unexpected Shell accent syntax")
        prop = match[1]
        role = "accent_fill" if "background" in prop else "accent_text"
        line = re.sub(r"st-mix\(-st-accent-color, #ffffff, 60%\)", colors[role], line)
        line = re.sub(
            r"st-lighten\(-st-accent-color, (\d+)%\)",
            lambda m: (
                colors["accent_fill_hover"]
                if role == "accent_fill"
                else colors["accent_text_hover" if int(m[1]) >= 20 and prop != "link-color" else "accent_text"]
            ),
            line,
        )
        line = re.sub(
            r"st-darken\(-st-accent-color, (\d+)%\)",
            lambda m: (
                colors["accent_text"]
                if role == "accent_text"
                else colors[
                    {14: "accent_fill", 10: "accent_fill_hover"}.get(
                        int(m[1]), "accent_fill_pressed"
                    )
                ]
            ),
            line,
        )
        line = line.replace("-st-accent-fg-color", colors["foreground"])
        line = line.replace("-st-accent-color", colors[role])
        lines.append(line)
    return "".join(lines)


def finalize(root, css, version):
    colors = palette.load_colors(root / "palette/colors.json")
    if version == "51":
        result = shell_preset(css, colors)
        if "-st-accent" in result:
            raise ValueError("unresolved Shell system accent")
        return result
    derived = root / "gnome-shell/assets/46-themed"
    assets = {
        name: shell46_asset((root / "gnome-shell/assets/46" / name).read_text(), colors)
        for name in CONTROLS
    }
    for name in CONTROLS:
        css = css.replace("assets/46/" + name, "assets/46-themed/" + name)
    derived.mkdir(parents=True, exist_ok=True)
    for name, text in assets.items():
        target = derived / name
        if not target.is_file() or target.read_text() != text:
            target.write_text(text)
    return css


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--version", choices=("46", "51"), required=True)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = finalize(args.root, args.input.read_text(), args.version)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Shell palette error: {error}\n")
    args.output.write_text(result)


if __name__ == "__main__":
    main()
