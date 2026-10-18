#!/usr/bin/env python3
"""Render development-only palette templates, or check committed outputs."""

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\{\{([a-z][a-z0-9_]*)(?:\.(hex|upper|hex_upper|r|g|b))?\}\}")
OUTPUT_ROOTS = {
    "src",
    "gtk-2.0",
    "gtk-4.0",
    "cinnamon",
    "gnome-shell",
    "metacity-1",
    "openbox-3",
    "extra",
}


def load_colors(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate palette key: {key}")
            result[key] = value
        return result

    palette = json.loads(path.read_text(), object_pairs_hook=unique)
    if (
        not isinstance(palette, dict)
        or set(palette) != {"version", "colors"}
        or palette["version"] != 1
    ):
        raise ValueError("expected palette version 1 and colors")
    colors = palette["colors"]
    if not isinstance(colors, dict) or not colors:
        raise ValueError("palette colors must be a nonempty object")
    for name, value in colors.items():
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]*", name)
            or not isinstance(value, str)
            or not re.fullmatch(r"#[0-9a-f]{6}", value)
        ):
            raise ValueError(f"invalid palette color: {name}")
    return colors


def render(text, colors):
    def replace(match):
        name, form = match.groups()
        if name not in colors:
            raise ValueError(f"unknown palette token: {name}")
        value = colors[name]
        if form in ("r", "g", "b"):
            start = {"r": 1, "g": 3, "b": 5}[form]
            return str(int(value[start : start + 2], 16))
        if form in ("hex", "hex_upper"):
            value = value[1:]
        return value.upper() if form in ("upper", "hex_upper") else value

    result = TOKEN.sub(replace, text)
    if "{{" in result:
        raise ValueError("invalid or unresolved palette placeholder")
    return result.encode("utf-8")


def outputs(root):
    colors = load_colors(root / "palette/colors.json")
    templates = root / "palette/templates"
    rendered = {}
    for template in sorted(templates.rglob("*.in")):
        name = template.relative_to(templates).with_suffix("")
        if (
            name.parts[0] not in OUTPUT_ROOTS
            or "upstream" in name.parts
            or name.suffix == ".gresource"
            or name.is_relative_to("gnome-shell/assets")
            or (name.parent == Path("gnome-shell") and name.suffix == ".css")
        ):
            raise ValueError(f"unsupported palette output: {name}")
        target = root / name
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"palette output escapes checkout: {name}")
        rendered[name] = render(template.read_text(), colors)
    if not rendered:
        raise ValueError("no palette templates found")
    return rendered


def generate(root, check=False):
    # Render and validate everything before writing any output.
    rendered = outputs(root)
    changed = []
    for name, data in rendered.items():
        target = root / name
        if target.is_file() and target.read_bytes() == data:
            continue
        changed.append(name)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail on stale outputs without changing files",
    )
    args = parser.parse_args()
    try:
        changed = generate(ROOT, check=args.check)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Palette error: {error}\n")
    for name in changed:
        print(f"{'Stale' if args.check else 'Generated'}: {name}")
    if args.check and changed:
        parser.exit(
            1,
            "Run python3 tools/generate_palette.py, then rebuild the GTK and Shell outputs.\n",
        )
    print(
        f"Palette {'check' if args.check else 'generation'} complete; {len(changed)} changed files."
    )


if __name__ == "__main__":
    main()
