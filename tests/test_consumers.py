"""Additional native consumers; run under Xvfb with tests/README prerequisites."""

import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConsumerTests(unittest.TestCase):
    def native(self, script, *arguments):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(
                os.environ.get("THEME_TEST_OUTPUT", temporary)
            ) / script.removesuffix(".py")
            output.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tests" / script),
                    *arguments,
                    str(ROOT),
                    str(output),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            print(result.stdout.strip())

    def test_qt5_native_palette(self):
        self.native("qt_colors.py", "5")

    def test_qt6_native_palette(self):
        self.native("qt_colors.py", "6")

    def test_qt5_slider_visibility_and_native_geometry(self):
        self.native("qt_sliders.py", "5")

    def test_qt6_slider_visibility_and_native_geometry(self):
        self.native("qt_sliders.py", "6")

    def test_gtk2_style_and_painted_button_contrast(self):
        self.native("gtk2_colors.py")

    def test_bat_native_theme_cache_and_highlighting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config/bat"
            (config / "themes").mkdir(parents=True)
            shutil.copyfile(ROOT / "extra/bat/config", config / "config")
            shutil.copyfile(
                ROOT / "extra/bat/themes/adwaita-amoled.tmTheme",
                config / "themes/adwaita-amoled.tmTheme",
            )
            env = dict(
                os.environ,
                XDG_CONFIG_HOME=str(root / "config"),
                XDG_CACHE_HOME=str(root / "cache"),
            )
            result = subprocess.run(
                ["batcat", "cache", "--build"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(
                ["batcat", "--color=always", "--style=plain", str(ROOT / "build.sh")],
                env=env,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"\x1b[", result.stdout)

    def test_rofi_native_theme_parser(self):
        result = subprocess.run(
            [
                "rofi",
                "-theme",
                str(ROOT / "extra/rofi/adwaita-dark.rasi"),
                "-dump-theme",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("parser error", result.stderr.lower())
        self.assertIn("element selected", result.stdout)

    def test_all_svg_assets_render_with_librsvg(self):
        with tempfile.TemporaryDirectory() as temporary:
            files = list(ROOT.rglob("*.svg"))
            self.assertGreater(len(files), 50)
            for index, source in enumerate(files):
                with self.subTest(path=str(source.relative_to(ROOT))):
                    output = Path(temporary) / f"{index}.png"
                    result = subprocess.run(
                        [
                            "rsvg-convert",
                            "--keep-aspect-ratio",
                            "--width",
                            "64",
                            "--height",
                            "64",
                            "--output",
                            str(output),
                            str(source),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    data = output.read_bytes()
                    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                    width, height = struct.unpack(">II", data[16:24])
                    self.assertGreater(width * height, 0)
            print(f"Rendered {len(files)} SVG assets using librsvg")


if __name__ == "__main__":
    from report import main

    main()
