"""Pinned folder artwork, palette derivatives and real optional installation."""
import configparser
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import unittest
import xml.etree.ElementTree as ET

import test_installer as base

sys.path.insert(0, str(base.ROOT / "tools"))
import generate_icons as icons
import generate_palette as palette

NAMES = ("blue", "yellow", "gold", "purple", "green", "red", "orange", "pink")
PREFIX = "extra/icons/Adwaita-AMOLED/"


class IconTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    fake_program = base.InstallerTests.fake_program
    write = base.InstallerTests.write

    def icon_root(self):
        return self.data / "icons" / base.THEME

    def test_generated_outputs_and_all_presets_match_palette_and_shape(self):
        baseline = (base.ROOT / icons.UPSTREAM / "Adwaita/scalable/places/folder.svg").read_text()
        for accent in NAMES:
            with self.subTest(accent=accent):
                colors = palette.preset_colors(base.ROOT, accent)
                expected = icons.files(base.ROOT, colors, accent)
                for name, data in expected.items():
                    override = base.ROOT / "accents" / accent / name
                    path = override if accent != "blue" and override.is_file() else base.ROOT / name
                    self.assertEqual(path.read_bytes(), data, str(path))
                text = expected[PREFIX + "scalable/places/folder.svg"].decode()
                self.assertIn(colors["accent_text"], text)
                self.assertIn(colors["accent_fill_pressed"], text)
                from test_accents import contrast
                self.assertGreaterEqual(contrast(colors["accent_fill_pressed"], colors["accent_text"]), 3)
                before = ET.fromstring(baseline)
                after = ET.fromstring(text)
                self.assertEqual([e.get("d") for e in before.iter() if e.get("d")],
                                 [e.get("d") for e in after.iter() if e.get("d")])
                for name, data in expected.items():
                    if name.endswith(".svg"):
                        svg = ET.fromstring(data)
                        self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
                        self.assertTrue(any(e.get("d") for e in svg.iter()))
                self.assertFalse(any("symbolic" in name for name in expected))

    def test_optional_install_all_colors_update_and_removal(self):
        self.run_cli()
        root = self.icon_root()
        self.assertFalse(root.exists())
        for accent in NAMES:
            self.run_cli("--icons", "--accent", accent)
            self.assertEqual((root / "accent-name").read_text(), accent + "\n")
            for name, data in icons.files(base.ROOT, palette.preset_colors(base.ROOT, accent), accent).items():
                self.assertEqual((root / name.removeprefix(PREFIX)).read_bytes(), data)
            subprocess.run(["sha256sum", "--check", "--status", "SHA256SUMS"], cwd=root, check=True)
        self.run_cli("--icons")
        self.assertEqual((root / "accent-name").read_text(), "pink\n")
        self.run_cli("--icons", "--remove")
        self.assertFalse(root.exists())

    def test_missing_adwaita_and_invalid_destinations_stop_before_changes(self):
        env = dict(self.env, XDG_DATA_DIRS=str(self.base / "no-system-icons"))
        result = self.run_cli("--icons", success=False, env=env)
        self.assertIn("Install adwaita-icon-theme", result.stderr)
        self.assertFalse(self.theme.exists())
        self.write(self.data / "icons/Adwaita/index.theme", "[Icon Theme]\nName=Adwaita\n")
        self.run_cli("--icons", "--dry-run", env=env)
        self.assertFalse(self.theme.exists())
        self.assertFalse(self.icon_root().exists())
        for directory in [self.data / "themes", self.theme / "nested", base.ROOT / "extra", self.home / ".themes"]:
            self.run_cli("--icons", "--icon-dest", str(directory), success=False)
            self.assertFalse(self.theme.exists())

    def test_unlisted_files_checkouts_and_links_are_preserved(self):
        root = self.icon_root()
        for kind in ["custom", "git", "link"]:
            if root.exists(): shutil.rmtree(root)
            if kind == "link":
                root.parent.mkdir(parents=True, exist_ok=True)
                root.symlink_to(self.base / "unrelated")
            else:
                self.write(root / (".git/config" if kind == "git" else "my-icon.svg"), "keep")
            for args in [(), ("--remove",)]:
                self.run_cli("--icons", *args, success=False)
            self.assertTrue(os.path.lexists(root))
            self.assertFalse(self.theme.exists())
            if root.is_symlink(): root.unlink()

    def test_activation_is_separate_and_preview_does_not_write_settings(self):
        log = self.base / "settings.log"
        self.env["XDG_CURRENT_DESKTOP"] = "Cinnamon"
        self.env["ICON_TEST_LOG"] = str(log)
        self.fake_program("gsettings", '''case $1 in
get) echo "'Adwaita'" ;;
writable) echo true ;;
range) echo s ;;
set) printf '%s\\n' "$*" >> "$ICON_TEST_LOG" ;;
esac''')
        for desktop, schema in [("GNOME", "org.gnome.desktop.interface"),
                                ("Budgie:GNOME", "org.gnome.desktop.interface"),
                                ("X-Cinnamon:GNOME", "org.cinnamon.desktop.interface"),
                                ("MATE", "org.mate.interface")]:
            self.env["XDG_CURRENT_DESKTOP"] = desktop
            log.unlink(missing_ok=True)
            self.run_cli("--icons")
            self.assertFalse(log.exists())
            self.run_cli("--activate-icons", "--dry-run")
            self.assertFalse(log.exists())
            self.run_cli("--activate-icons")
            self.assertEqual(log.read_text(), f"set {schema} icon-theme Adwaita-AMOLED\n")
        self.env["XDG_CURRENT_DESKTOP"] = "XFCE:GNOME"
        log.unlink()
        self.fake_program("xfconf-query", 'printf "%s\\n" "$*" >> "$ICON_TEST_LOG"')
        self.run_cli("--activate-icons", "--dry-run")
        self.assertFalse(log.exists())
        self.run_cli("--activate-icons")
        self.assertEqual(log.read_text(), "-c xsettings -p /Net/IconThemeName --create -t string -s Adwaita-AMOLED\n")

    def test_archive_installs_icons_without_build_sources(self):
        archive = self.base / "icons.tar.gz"
        subprocess.run([sys.executable, str(base.ROOT / "tools/package.py"), str(archive)], check=True, capture_output=True)
        with tarfile.open(archive) as tar:
            tar.extractall(self.base / "release", filter="data")
        source = self.base / "release" / base.THEME
        self.assertFalse((source / "icons").exists())
        self.run_cli("--icons", "--accent", "purple", root=source)
        self.assertEqual((self.icon_root() / "accent-name").read_text(), "purple\n")
        config = configparser.ConfigParser()
        config.read(self.icon_root() / "index.theme")
        self.assertEqual(config["Icon Theme"]["Inherits"], "Adwaita,hicolor")

    def test_corrupt_icon_source_stops_before_installing_anything(self):
        source = self.base / "source"
        shutil.copytree(base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        (source / PREFIX / "scalable/places/folder.svg").write_text("corrupt")
        result = self.run_cli("--icons", root=source, success=False)
        self.assertIn("Folder icon checksum verification failed", result.stderr)
        self.assertFalse(self.theme.exists())
        self.assertFalse(self.icon_root().exists())

    def test_icon_staging_failure_preserves_the_previous_icon_theme(self):
        self.run_cli("--icons")
        root = self.icon_root()
        previous = (root / "scalable/places/folder.svg").read_bytes()
        self.env["ICON_SOURCE"] = str(self.theme / PREFIX)
        self.fake_program("cp", '''for value in "$@"; do
[[ $value != "$ICON_SOURCE/." ]] || { echo 'simulated icon copy failure' >&2; exit 1; }
done
exec /usr/bin/cp "$@"''')
        self.run_cli("--icons", "--accent", "red", success=False)
        self.assertEqual((root / "scalable/places/folder.svg").read_bytes(), previous)
        self.assertEqual((root / "accent-name").read_text(), "blue\n")
        self.assertFalse(list(root.parent.glob(".Adwaita-AMOLED-install.*")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
