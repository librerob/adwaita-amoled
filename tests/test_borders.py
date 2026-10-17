"""Native pixel regressions for decorative outlines and identifying input edges."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BorderTests(unittest.TestCase):
    def probe(self, version):
        with tempfile.TemporaryDirectory(prefix="amoled-borders-") as temporary:
            base = Path(temporary)
            (base / "themes").mkdir()
            (base / "themes/Adwaita-AMOLED").symlink_to(ROOT, target_is_directory=True)
            output = Path(os.environ.get("THEME_TEST_OUTPUT", temporary))
            env = dict(
                os.environ,
                XDG_DATA_HOME=str(base),
                XDG_CONFIG_HOME=str(base / "config"),
                GSETTINGS_BACKEND="memory",
                GTK_THEME="Adwaita-AMOLED",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tests/border_native.py"),
                    version,
                    str(output),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Theme parsing error", result.stderr)
            print(result.stdout)

    def test_gtk3_decorative_borders_and_input_edges(self):
        self.probe("3.0")

    def test_gtk4_decorative_borders_and_input_edges(self):
        self.probe("4.0")


if __name__ == "__main__":
    from report import main

    main()
