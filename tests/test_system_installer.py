"""Root-owned shared installation under a temporary staging parent only."""

import os
import unittest
import test_installer as base


class SystemInstallerTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli

    def test_shared_theme_ownership_readability_update_and_remove(self):
        self.assertEqual(
            os.geteuid(), 0, "Run this suite as root in temporary staging roots"
        )
        dest = self.base / "system/themes"
        for _ in range(2):
            self.run_cli("--system", "--dest", str(dest))
            theme = dest / base.THEME
            for path in theme.rglob("*"):
                self.assertEqual(path.stat().st_uid, 0)
                self.assertFalse(path.stat().st_mode & 0o022, str(path))
                self.assertTrue(path.stat().st_mode & 0o004, str(path))
                if path.is_dir():
                    self.assertTrue(path.stat().st_mode & 0o001, str(path))
            for version in ["3.0", "4.0"]:
                self.assertEqual(
                    (theme / f"gtk-{version}/gtk.gresource").read_bytes(),
                    (base.ROOT / f"gtk-{version}/gtk.gresource").read_bytes(),
                )
        self.assertFalse(self.config.exists())
        self.assertFalse((self.home / "state").exists())
        self.run_cli("--system", "--dest", str(dest), "--remove")
        self.assertFalse(theme.exists())

    def test_shared_scope_refuses_personal_configuration_before_copying(self):
        for args in [
            ("-l",),
            ("--extras", "qt"),
            ("--activate",),
            ("--flatpak", "org.example.App=modern"),
        ]:
            dest = self.base / "system/themes"
            self.run_cli("--system", "--dest", str(dest), *args, success=False)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    from report import main

    main()
