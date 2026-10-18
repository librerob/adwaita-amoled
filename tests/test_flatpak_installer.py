"""Per-app Bash commands and file paths; real sandbox execution is separate."""

import unittest
import test_installer as base


class FlatpakInstallerTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    fake_program = base.InstallerTests.fake_program

    def fake_flatpak(self):
        log = self.base / "flatpak-args"
        self.env["TEST_FLATPAK_LOG"] = str(log)
        self.fake_program(
            "flatpak",
            'if [[ $1 == info ]]; then exit 0; fi\nprintf "%s\\n" "$*" >> "$TEST_FLATPAK_LOG"',
        )
        return log

    def test_runtime_selection_is_explicit_and_independent_of_host(self):
        log = self.fake_flatpak()
        for mode, entry in [("legacy", "gtk.css"), ("modern", "gtk-modern.css")]:
            self.run_cli("--flatpak", "org.example.App=" + mode)
            css = self.home / ".var/app/org.example.App/config/gtk-4.0/gtk.css"
            self.assertEqual(css.resolve(), self.theme / "extra/libadwaita" / entry)
        self.assertIn(
            "--filesystem=" + str(self.theme) + ":ro org.example.App", log.read_text()
        )
        self.assertNotIn("--global", log.read_text())

    def test_gtk3_mode_sets_only_selected_app_theme(self):
        log = self.fake_flatpak()
        self.run_cli("--flatpak", "org.example.Old=gtk3")
        self.assertIn("--env=GTK_THEME=Adwaita-AMOLED org.example.Old", log.read_text())
        self.assertFalse(
            (self.home / ".var/app/org.example.Old/config/gtk-4.0").exists()
        )

    def test_selected_app_remove_keeps_host_theme_and_other_app(self):
        log = self.fake_flatpak()
        self.run_cli(
            "--flatpak", "org.example.One=legacy", "--flatpak", "org.example.Two=modern"
        )
        self.run_cli("--remove", "--flatpak", "org.example.One=legacy")
        self.assertTrue((self.theme / "index.theme").exists())
        self.assertEqual((self.home / ".themes" / base.THEME).resolve(), self.theme)
        self.assertTrue(
            (self.home / ".var/app/org.example.Two/config/gtk-4.0/gtk.css").exists()
        )
        self.assertFalse(
            (self.home / ".var/app/org.example.One/config/gtk-4.0/gtk.css").is_symlink()
        )
        self.assertIn(
            "--nofilesystem=" + str(self.theme) + " org.example.One", log.read_text()
        )
        self.assertNotIn("--reset", log.read_text())


if __name__ == "__main__":
    from report import main

    main()
