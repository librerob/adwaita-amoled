#!/usr/bin/env python3
"""Build sparse, precompiled accent overlays; users need only the Bash installer."""
import argparse
import hashlib
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

import generate_palette as palette

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("yellow", "gold", "purple", "green", "red", "orange", "pink")


def manifest(files):
    return "".join(
        hashlib.sha256(data).hexdigest() + "  " + name + "\n"
        for name, data in sorted(files.items())
    ).encode()


def xterm_index(color):
    """Nearest fixed xterm-256 color, excluding user-defined ANSI slots."""
    target = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
    levels = (0, 95, 135, 175, 215, 255)
    candidates = {
        16 + 36 * r + 6 * g + b: (levels[r], levels[g], levels[b])
        for r in range(6)
        for g in range(6)
        for b in range(6)
    }
    candidates.update({232 + i: (8 + i * 10,) * 3 for i in range(24)})
    return min(
        candidates,
        key=lambda index: sum((a - b) ** 2 for a, b in zip(target, candidates[index])),
    )


def airline_preset(text, colors):
    # True-color fields come from the shared template; Airline also needs its
    # separate indexed fallback updated. Keep all status/mode colors unchanged.
    for variable, role in (("blue", "accent_text"), ("blue_h", "accent_text_hover")):
        pattern = rf"(let s:{variable}\s*= \['#[0-9a-f]{{6}}', )\d+(\])"
        text, count = re.subn(
            pattern, lambda m: m[1] + str(xterm_index(colors[role])) + m[2], text
        )
        if count != 1:
            raise ValueError("unexpected Airline accent fallback: " + variable)
    return text


def shell46_asset(text, colors):
    """Derive preset controls without modifying the pinned blue SVG originals."""

    def style(match):
        value = match[1]
        role = "accent_text" if "fill:none;" in value else "accent_fill"
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
    """Resolve upstream's dynamic accent only in a named preset's compiled CSS.

    Preserve selectors, geometry and upstream sources. Text and opaque fills
    have separate contrast roles; the default blue build retains system hues.
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
                else colors["accent_text_hover" if int(m[1]) >= 20 else "accent_text"]
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


def build(root):
    runtime = (root / "runtime-files.txt").read_text().splitlines()
    result = {}
    with tempfile.TemporaryDirectory(prefix="amoled-accent-build-") as temporary:
        work = Path(temporary)
        for name in runtime:
            dest = work / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / name, dest)
        for folder in ["src", "palette", "gnome-shell/sass"]:
            shutil.copytree(root / folder, work / folder, dirs_exist_ok=True)
        for name in ["build.sh", "gnome-shell/build.sh"]:
            shutil.copy2(root / name, work / name)
        for accent in NAMES:
            colors = palette.preset_colors(root, accent)
            palette.generate(work, colors=colors)
            airline = work / "extra/nvim/autoload/airline/themes/adwaita_amoled.vim"
            airline.write_text(airline_preset(airline.read_text(), colors))
            for source in (root / "gnome-shell/assets/46").glob("*.svg"):
                if source.name.startswith(("checkbox", "toggle")):
                    target = work / source.relative_to(root)
                    target.write_text(shell46_asset(source.read_text(), colors))
            for args in [
                ["bash", str(work / "build.sh")],
                ["bash", str(work / "gnome-shell/build.sh")],
                ["bash", str(work / "gnome-shell/build.sh"), "--shell-version", "46"],
            ]:
                subprocess.run(args, check=True, capture_output=True, text=True)
            for name in [
                "gnome-shell/gnome-shell.css",
                "gnome-shell/gnome-shell-51.css",
            ]:
                p = work / name
                p.write_text(shell_preset(p.read_text(), colors))
            (work / "accent-name").write_text(accent + "\n")
            changed = {
                name: (work / name).read_bytes()
                for name in runtime
                if (work / name).read_bytes() != (root / name).read_bytes()
            }
            changed["SHA256SUMS"] = manifest(changed)
            result.update({accent + "/" + name: data for name, data in changed.items()})
    result["SHA256SUMS"] = manifest(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files = build(ROOT)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Accent build failed: {error}\n")
    directory = ROOT / "accents"
    existing = (
        {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}
        if directory.exists()
        else set()
    )
    if existing - files.keys():
        parser.exit(
            1, "Unexpected files in accents/; inspect them before rebuilding.\n"
        )
    changed = [
        name
        for name, data in files.items()
        if not (directory / name).is_file() or (directory / name).read_bytes() != data
    ]
    if args.check and changed:
        parser.exit(1, "Stale accent outputs: " + ", ".join(changed) + "\n")
    if not args.check:
        for name in changed:
            dest = directory / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(files[name])
    print(
        f"Accent {'check' if args.check else 'build'} complete: {len(changed)} changed files, seven presets."
    )


if __name__ == "__main__":
    main()
