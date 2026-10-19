"""Protect checkouts/local data and remove only theme-owned GTK4 links."""

import os
from pathlib import Path
import unittest

import test_installer as base


class PreservationTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    write = base.InstallerTests.write
    fake_program = base.InstallerTests.fake_program

    def test_explicit_gtk4_replacement_warns_before_mutations_and_in_preview(self):
        custom = self.config / "gtk-4.0/gtk.css"
        asset = self.config / "gtk-4.0/assets/custom.txt"
        self.write(custom, "custom CSS")
        self.write(asset, "custom asset")
        self.fake_program(
            "mkdir", 'printf "MUTATION: mkdir\\n" >&2; exec /usr/bin/mkdir "$@"'
        )
        args = ("-l", "--gtk4-mode", "legacy")
        preview = self.run_cli(*args, "--dry-run")
        self.assertIn("without --dry-run would replace", preview.stderr)
        self.assertNotIn("MUTATION:", preview.stderr)
        self.assertEqual(custom.read_text(), "custom CSS")
        self.assertEqual(asset.read_text(), "custom asset")
        self.assertFalse(self.theme.exists())
        result = self.run_cli(*args)
        for output in (preview.stderr, result.stderr):
            for name in ("gtk.css", "gtk-dark.css", "libadwaita-tweaks.css", "assets"):
                self.assertIn(str(self.config / "gtk-4.0" / name), output)
            self.assertIn("entire assets directory", output)
            self.assertIn("No backups are made", output)
            self.assertIn("Omit -l/--libadwaita", output)
        self.assertLess(result.stderr.index("WARNING:"), result.stderr.index("MUTATION:"))
        self.assertTrue(custom.is_symlink())
        self.assertFalse(asset.exists())
        for options in [("--dry-run",), ("--remove", "-l")]:
            self.assertNotIn("WARNING:", self.run_cli(*options).stderr)

    def test_legacy_checkout_blocks_all_replacements_and_removal(self):
        self.run_cli()
        previous = self.theme / "README.md"
        previous.write_text("existing installed theme")
        legacy = self.home / ".themes" / base.THEME
        legacy.unlink()
        self.write(legacy / ".git/config", "repository metadata")
        self.write(legacy / "src/local-change.css", "local edits")
        custom = self.config / "gtk-4.0/gtk.css"
        self.write(custom, "custom CSS")
        for args in [("-l", "--gtk4-mode", "legacy"), ("--remove",)]:
            result = self.run_cli(*args, success=False)
            self.assertIn("Git checkout", result.stderr)
            self.assertEqual(previous.read_text(), "existing installed theme")
            self.assertEqual(
                (legacy / ".git/config").read_text(), "repository metadata"
            )
            self.assertEqual(
                (legacy / "src/local-change.css").read_text(), "local edits"
            )
            self.assertEqual(custom.read_text(), "custom CSS")

    def test_git_directory_file_and_dangling_link_are_all_protected(self):
        for kind in ("directory", "worktree-file", "dangling-link"):
            with self.subTest(kind=kind):
                destination = self.base / kind
                git = destination / base.THEME / ".git"
                git.parent.mkdir(parents=True)
                if kind == "directory":
                    self.write(git / "config", "keep")
                elif kind == "worktree-file":
                    git.write_text("gitdir: /some/other/repository")
                else:
                    git.symlink_to(self.base / "missing-git-directory")
                for args in [(), ("--remove",)]:
                    result = self.run_cli(
                        "--dest", str(destination), *args, success=False
                    )
                    self.assertIn("Git checkout", result.stderr)
                    self.assertTrue(os.path.lexists(git))

    def test_unlisted_local_files_and_hidden_directories_are_preserved(self):
        self.run_cli()
        paths = [
            self.theme / "gtk-3.0/my-notes.txt",
            self.theme / ".local-data/private.txt",
        ]
        for path in paths:
            self.write(path, "keep personal data")
        before = (self.theme / "gtk-3.0/gtk.gresource").read_bytes()
        for args in [(), ("--remove",), ("--dry-run",)]:
            result = self.run_cli(*args, success=False)
            self.assertIn("Keeping local", result.stderr)
            for path in paths:
                self.assertEqual(path.read_text(), "keep personal data")
            self.assertEqual(
                (self.theme / "gtk-3.0/gtk.gresource").read_bytes(), before
            )

    def test_obsolete_files_in_installed_runtime_manifest_do_not_block_updates(self):
        self.run_cli()
        old = self.theme / "gtk-3.0/obsolete-theme-asset.svg"
        self.write(old, "old runtime asset")
        listing = self.theme / "runtime-files.txt"
        listing.write_text(listing.read_text() + "gtk-3.0/obsolete-theme-asset.svg\n")
        self.run_cli()
        self.assertFalse(old.exists())
        self.assertEqual(
            listing.read_bytes(), (base.ROOT / "runtime-files.txt").read_bytes()
        )

    def test_unlisted_symlink_keeps_external_data_and_installed_theme(self):
        self.run_cli()
        external = self.base / "external"
        self.write(external / "private.txt", "keep outside data")
        link = self.theme / "personal-directory"
        link.symlink_to(external)
        for args in [(), ("--remove",)]:
            self.run_cli(*args, success=False)
            self.assertTrue(link.is_symlink())
            self.assertEqual(
                (external / "private.txt").read_text(), "keep outside data"
            )
            self.assertTrue((self.theme / "gtk-3.0/gtk.gresource").exists())

    def test_unreadable_runtime_directory_is_not_silently_replaced(self):
        self.assertNotEqual(
            os.geteuid(), 0, "Run user preservation tests as a normal user"
        )
        self.run_cli()
        directory = self.theme / "gtk-3.0"
        directory.chmod(0)
        try:
            result = self.run_cli(success=False)
            self.assertIn("Cannot inspect installed directory", result.stderr)
        finally:
            directory.chmod(0o755)
        self.assertTrue((directory / "gtk.gresource").exists())

    def test_invalid_installed_manifest_keeps_all_files_and_external_data(self):
        self.run_cli()
        outside = self.base / "private.txt"
        outside.write_text("outside data")
        listing = self.theme / "runtime-files.txt"
        listing.write_text(listing.read_text() + "../private.txt\n")
        for args in [(), ("--remove",)]:
            self.run_cli(*args, success=False)
            self.assertTrue(self.theme.exists())
            self.assertEqual(outside.read_text(), "outside data")

    def test_plain_removal_cleans_all_four_owned_native_links(self):
        self.run_cli("-l", "--gtk4-mode", "legacy")
        directory = self.config / "gtk-4.0"
        paths = [
            directory / name
            for name in ("gtk.css", "gtk-dark.css", "libadwaita-tweaks.css", "assets")
        ]
        self.assertTrue(all(path.is_symlink() for path in paths))
        self.run_cli("--remove", "--dry-run")
        self.assertTrue(all(path.is_symlink() and path.exists() for path in paths))
        self.run_cli("--remove")
        self.assertTrue(all(not os.path.lexists(path) for path in paths))

    def test_plain_removal_keeps_custom_files_and_foreign_links(self):
        self.run_cli("-l", "--gtk4-mode", "legacy")
        directory = self.config / "gtk-4.0"
        css = directory / "gtk.css"
        css.unlink()
        css.write_text("custom replacement")
        foreign = self.base / "another-theme.css"
        foreign.write_text("another theme")
        dark = directory / "gtk-dark.css"
        dark.unlink()
        dark.symlink_to(foreign)
        self.write(directory / "settings.ini", "personal settings")
        self.run_cli("--remove")
        self.assertEqual(css.read_text(), "custom replacement")
        self.assertEqual(dark.resolve(), foreign)
        self.assertEqual(foreign.read_text(), "another theme")
        self.assertEqual((directory / "settings.ini").read_text(), "personal settings")
        self.assertFalse(os.path.lexists(directory / "assets"))
        self.assertFalse(os.path.lexists(directory / "libadwaita-tweaks.css"))


if __name__ == "__main__":
    from report import main

    main()
