"""Execute documented manual commands and verify repeat copies and real backups."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManualInstallationTests(unittest.TestCase):
    def run_bash(self, text, env):
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-euc", text],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_readme_and_guide_runtime_copy_commands(self):
        for filename, heading in [
            ("README.md", "### Manual installation"),
            ("INSTALLING.md", "### Theme files and desktop selection"),
        ]:
            with self.subTest(
                document=filename
            ), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / "data"))
                text = (ROOT / filename).read_text().split(heading, 1)[1]
                command = re.search(r"```bash\n(.*?)```", text, re.S)[1]
                for _ in range(2):
                    self.run_bash(command, env)
                theme = home / "data/themes/Adwaita-AMOLED"
                for version in ["3.0", "4.0"]:
                    self.assertEqual(
                        (theme / f"gtk-{version}/gtk.gresource").read_bytes(),
                        (ROOT / f"gtk-{version}/gtk.gresource").read_bytes(),
                    )
                self.assertFalse((theme / "gtk-3.0/gtk-3.0").exists())
                self.assertTrue((theme / "extra/libadwaita/gtk-modern.css").is_file())

    def test_both_documented_gtk4_entry_points_updates_and_backup(self):
        text = (
            (ROOT / "INSTALLING.md")
            .read_text()
            .split("### GTK4 and libadwaita overrides", 1)[1]
            .split("### Manual extras", 1)[0]
        )
        blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
        self.assertEqual(len(blocks), 3)
        for entry, selection in [("gtk-modern.css", blocks[1]), ("gtk.css", blocks[2])]:
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                env = dict(
                    os.environ,
                    HOME=str(home),
                    XDG_DATA_HOME=str(home / "data"),
                    XDG_CONFIG_HOME=str(home / "config"),
                )
                theme = home / "data/themes/Adwaita-AMOLED"
                import shutil

                shutil.copytree(ROOT / "extra/libadwaita", theme / "extra/libadwaita")
                config = home / "config/gtk-4.0"
                config.mkdir(parents=True)
                (config / "gtk.css").write_text("/* original custom CSS */\n")
                asset = next((theme / "extra/libadwaita/assets").glob("*.svg"))
                for n in range(3):
                    asset.write_bytes(
                        asset.read_bytes() + f"\n<!-- change {n} -->\n".encode()
                    )
                    self.run_bash(blocks[0] + "\n" + selection, env)
                    self.assertEqual(
                        (config / "gtk.css").read_bytes(),
                        (theme / "extra/libadwaita" / entry).read_bytes(),
                    )
                    self.assertEqual(
                        (config / "assets" / asset.name).read_bytes(),
                        asset.read_bytes(),
                    )
                    self.assertFalse((config / "assets/assets").exists())
                backups = list(config.parent.glob("gtk-4.0.backup.*"))
                self.assertEqual(len(backups), 3)
                self.assertTrue(
                    any(
                        (p / "gtk.css").read_text() == "/* original custom CSS */\n"
                        for p in backups
                    )
                )


if __name__ == "__main__":
    from report import main

    main()
