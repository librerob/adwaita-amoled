"""Measured presets and real Bash installation of precompiled color overlays."""

import hashlib
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tarfile
import tomllib
import unittest

import test_installer as base

sys.path.insert(0, str(base.ROOT / "tools"))
import generate_palette as palette
import package as packaging
from test_shell import rules

COLORS = ("yellow", "gold", "purple", "green", "red", "orange", "pink")


def luminance(value):
    channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return sum(
        (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) * w
        for c, w in zip(channels, (0.2126, 0.7152, 0.0722))
    )


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class AccentTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    fake_program = base.InstallerTests.fake_program

    def expected(self, accent, name):
        override = base.ROOT / "accents" / accent / name
        return override if accent != "blue" and override.is_file() else base.ROOT / name

    def test_measured_presets_keep_semantics_and_readable_roles(self):
        original = palette.preset_colors(base.ROOT, "blue")
        for accent in COLORS:
            with self.subTest(accent=accent):
                colors = palette.preset_colors(base.ROOT, accent)
                for role, value in original.items():
                    if not role.startswith("accent_"):
                        self.assertEqual(colors[role], value)
                for background in [
                    "#000000",
                    "#0f0f0f",
                    "#141414",
                    "#1a1a1a",
                    "#252525",
                    colors["accent_surface"],
                    colors["accent_selection"],
                ]:
                    self.assertGreaterEqual(
                        contrast(colors["accent_text"], background), 7
                    )
                for role in [
                    "accent_fill",
                    "accent_fill_hover",
                    "accent_fill_pressed",
                    "accent_checked",
                    "accent_gradient_start",
                    "accent_gradient_end",
                    "accent_deep",
                    "accent_deeper",
                    "accent_deepest",
                ]:
                    self.assertGreaterEqual(
                        contrast("#ffffff", colors[role]), 4.5, role
                    )
                self.assertGreaterEqual(contrast(colors["accent_fill"], "#252525"), 3)

    def test_distribution_hashes_and_all_seven_identities(self):
        names = packaging.accent_paths(base.ROOT)
        for accent in COLORS:
            self.assertIn(f"accents/{accent}/SHA256SUMS", names)
            self.assertEqual(
                (base.ROOT / "accents" / accent / "accent-name").read_text(),
                accent + "\n",
            )

    def test_terminal_ansi_slots_keep_their_meanings_across_accents(self):
        def kitty(path):
            return {
                key: value
                for key, value in (
                    line.split(None, 1)
                    for line in path.read_text().splitlines()
                    if line and not line.startswith("#")
                )
                if key.startswith("color") and key[5:].isdigit()
            }

        normal = kitty(base.ROOT / "extra/kitty/adwaita-amoled.conf")
        alacritty = tomllib.loads(
            (base.ROOT / "extra/alacritty/alacritty.toml").read_text()
        )["colors"]
        for accent in COLORS:
            with self.subTest(accent=accent):
                self.assertEqual(
                    kitty(self.expected(accent, "extra/kitty/adwaita-amoled.conf")),
                    normal,
                )
                colors = tomllib.loads(
                    self.expected(accent, "extra/alacritty/alacritty.toml").read_text()
                )["colors"]
                for group in ("normal", "bright", "dim"):
                    self.assertEqual(colors[group], alacritty[group])

    def test_presets_preserve_shell_layout_and_resolve_system_accent_expressions(self):
        properties = {
            "color",
            "background",
            "background-color",
            "background-image",
            "border",
            "border-color",
            "box-shadow",
            "-arrow-background-color",
            "-arrow-border-color",
            "-barlevel-overdrive-color",
            "warning-color",
        }
        for version in ("46", "51"):
            name = f"gnome-shell/gnome-shell-{version}.css"
            original = rules((base.ROOT / name).read_text())
            for accent in ("blue", *COLORS):
                with self.subTest(accent=accent, version=version):
                    text = self.expected(accent, name).read_text()
                    self.assertNotIn("-st-accent", text)
                    changed = rules(text)
                    self.assertEqual(len(original), len(changed))
                    for (selector, before), (new_selector, after) in zip(
                        original, changed
                    ):
                        self.assertEqual(selector, new_selector)
                        self.assertEqual(
                            [key for key, _ in before], [key for key, _ in after]
                        )
                        for (key, value), (_, new_value) in zip(before, after):
                            if key not in properties and not key.endswith("-color"):
                                self.assertEqual(value, new_value, f"{selector}: {key}")

    def test_all_shell46_presets_use_derived_palette_controls_and_keep_originals(self):
        import shell_palette

        for accent in ("blue", *COLORS):
            colors = palette.preset_colors(base.ROOT, accent)
            css = self.expected(accent, "gnome-shell/gnome-shell-46.css").read_text()
            for name in shell_palette.CONTROLS:
                with self.subTest(accent=accent, asset=name):
                    source = base.ROOT / "gnome-shell/assets/46" / name
                    expected = shell_palette.shell46_asset(source.read_text(), colors)
                    actual = self.expected(accent, "gnome-shell/assets/46-themed/" + name)
                    self.assertEqual(actual.read_text(), expected)
                    self.assertNotIn("assets/46/" + name, css)
                    self.assertIn("assets/46-themed/" + name, css)
                    self.assertFalse((base.ROOT / "accents" / accent / "gnome-shell/assets/46" / name).exists())

    def test_every_installed_file_matches_selected_variant_and_retains_color(self):
        listing = (base.ROOT / "runtime-files.txt").read_text().splitlines()
        for accent in COLORS:
            with self.subTest(accent=accent):
                self.run_cli(
                    "--accent", accent, "--shell-version", "46", "--extras", "qt,kitty"
                )
                for name in listing:
                    expected = (
                        "gnome-shell/gnome-shell-46.css"
                        if name == "gnome-shell/gnome-shell.css"
                        else name
                    )
                    self.assertEqual(
                        (self.theme / name).read_bytes(),
                        self.expected(accent, expected).read_bytes(),
                        name,
                    )
                for extra in [
                    "qt5ct/colors/Adwaita-AMOLED.conf",
                    "kitty/themes/adwaita-amoled.conf",
                ]:
                    source = "extra/" + extra.replace("kitty/themes/", "kitty/")
                    self.assertEqual(
                        (self.config / extra).read_bytes(),
                        self.expected(accent, source).read_bytes(),
                    )
                self.assertFalse((self.theme / "accents").exists())
                self.run_cli()
                self.assertEqual(
                    (self.theme / "accent-name").read_text(), accent + "\n"
                )
        self.run_cli("--accent", "blue")
        self.assertEqual(
            (self.theme / "gtk-3.0/gtk.gresource").read_bytes(),
            (base.ROOT / "gtk-3.0/gtk.gresource").read_bytes(),
        )

    def test_color_preview_and_invalid_color_do_not_replace_existing_theme(self):
        self.run_cli("--accent", "gold")
        before = (self.theme / "gtk-3.0/gtk.gresource").read_bytes()
        self.run_cli("--accent", "pink", "--dry-run")
        for value in ["../gold", "/tmp/gold", "teal", "Gold"]:
            self.run_cli("--accent", value, success=False)
        self.assertEqual((self.theme / "gtk-3.0/gtk.gresource").read_bytes(), before)
        self.assertEqual((self.theme / "accent-name").read_text(), "gold\n")
        self.run_cli("--remove")
        self.assertFalse(self.theme.exists())

    def test_corrupt_overlay_is_rejected_before_replacing_installed_files(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        self.run_cli("--accent", "purple")
        before = (self.theme / "gtk-3.0/gtk.gresource").read_bytes()
        (source / "accents/gold/gtk-3.0/gtk.gresource").write_bytes(b"damaged")
        self.run_cli("--accent", "gold", root=source, success=False)
        self.assertEqual((self.theme / "gtk-3.0/gtk.gresource").read_bytes(), before)

    def test_selected_directory_and_file_symlinks_are_rejected(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        file = source / "accents/gold/accent-name"
        file.unlink()
        file.symlink_to(source / "accent-name")
        self.run_cli("--accent", "gold", root=source, success=False)
        self.assertFalse(self.theme.exists())

    def test_app_extras_ignore_files_not_in_the_verified_overlay_manifest(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        name = "extra/qt5ct/qss/fusion-simple-scrollbar.qss"
        unlisted = source / "accents/gold" / name
        self.assertFalse(unlisted.exists())
        unlisted.parent.mkdir(parents=True, exist_ok=True)
        unlisted.write_text("unlisted local file")
        self.run_cli("--accent", "gold", "--extras", "qt", root=source)
        self.assertEqual(
            (self.config / "qt5ct/qss/fusion-simple-scrollbar.qss").read_bytes(),
            (base.ROOT / name).read_bytes(),
        )

    def test_overlay_copy_failure_and_staged_corruption_keep_the_previous_theme(self):
        self.run_cli("--accent", "gold")
        before = (self.theme / "gtk-3.0/gtk.gresource").read_bytes()
        real_cp = shlex.quote(shutil.which("cp"))
        for failure in ("exit 23", 'printf damaged > "${@: -1}/gtk-3.0/gtk.gresource"'):
            with self.subTest(failure=failure):
                self.fake_program(
                    "cp",
                    f'if [[ $PWD == */accents/pink ]]; then\n{real_cp} "$@"\n{failure}\nelse\nexec {real_cp} "$@"\nfi',
                )
                self.run_cli("--accent", "pink", success=False)
                self.assertEqual(
                    (self.theme / "gtk-3.0/gtk.gresource").read_bytes(), before
                )
                self.assertEqual((self.theme / "accent-name").read_text(), "gold\n")
                self.assertFalse(
                    list(self.theme.parent.glob(".Adwaita-AMOLED-install.*"))
                )

    def test_malformed_manifest_does_not_copy_unlisted_or_escaping_files(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        manifest = source / "accents/gold/SHA256SUMS"
        original = manifest.read_text()
        digest = hashlib.sha256(b"unused").hexdigest()
        for text in (
            original + original.splitlines()[0] + "\n",
            original + digest + "  ../outside\n",
            original + digest + "  tools/anything\n",
            original.replace("  accent-name\n", "  unknown\n"),
        ):
            with self.subTest(text=text[-90:]):
                manifest.write_text(text)
                self.run_cli("--accent", "gold", root=source, success=False)
                self.assertFalse(self.theme.exists())

    def test_materialized_css_urls_resolve_to_shared_or_overridden_runtime_assets(self):
        import re

        for accent in COLORS:
            with self.subTest(accent=accent):
                self.run_cli("--accent", accent)
                for path in self.theme.rglob("*"):
                    if path.suffix not in (".css", ".qss", ".rasi"):
                        continue
                    text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
                    for url in re.findall(
                        r"""url\(\s*['"]?([^)'"\s]+)['"]?\s*\)""", text
                    ):
                        if not re.match(r"(resource|data|https?):", url):
                            self.assertTrue(
                                (path.parent / url).is_file(),
                                f"{accent}: {path}: {url}",
                            )

    def test_archive_install_contains_color_choices_without_installing_all_variants(
        self,
    ):
        archive = self.base / "colors.tar.gz"
        subprocess.run(
            [sys.executable, str(base.ROOT / "tools/package.py"), str(archive)],
            check=True,
            capture_output=True,
        )
        with tarfile.open(archive) as package:
            package.extractall(self.base / "extracted", filter="data")
        root = self.base / "extracted/Adwaita-AMOLED"
        self.run_cli("--accent", "red", root=root)
        self.assertEqual((self.theme / "accent-name").read_text(), "red\n")
        self.assertEqual(
            (self.theme / "gtk-4.0/gtk.gresource").read_bytes(),
            self.expected("red", "gtk-4.0/gtk.gresource").read_bytes(),
        )
        self.assertFalse((self.theme / "accents").exists())


if __name__ == "__main__":
    from report import main

    main()
