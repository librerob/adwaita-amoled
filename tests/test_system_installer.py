"""Root-owned shared installation under a temporary staging parent only."""

import os
import json
import subprocess
import sys
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
            ("--prefer-dark",),
            ("--flatpak", "org.example.App=modern"),
        ]:
            dest = self.base / "system/themes"
            self.run_cli("--system", "--dest", str(dest), *args, success=False)
            self.assertFalse(dest.exists())

    def test_root_gtk2_discovers_the_root_owned_shared_link(self):
        dest = self.base / "local/share/themes"
        links = self.base / "usr/share/themes"
        self.run_cli("--system", "--dest", str(dest), "--link", str(links))
        env = dict(self.env, GTK_DATA_PREFIX=str(self.base / "usr"))
        for key in ("GTK_THEME", "GTK2_RC_FILES", "GTK_PATH"):
            env.pop(key, None)
        result = subprocess.run(
            [sys.executable, str(base.ROOT / "tests/installed_gtk2.py")],
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["normal_theme_discovery"])

    def test_new_shared_parent_is_accessible_with_restrictive_root_umask(self):
        self.assertEqual(os.geteuid(), 0)
        dest = self.base / "shared/themes"
        original = os.umask(0o077)
        try:
            self.run_cli("--system", "--dest", str(dest))
        finally:
            os.umask(original)
        self.assertEqual(dest.stat().st_mode & 0o777, 0o755)

    def test_root_owned_shared_link_update_and_remove(self):
        self.assertEqual(os.geteuid(), 0)
        dest = self.base / "local/share/themes"
        links = self.base / "usr/share/themes"
        for _ in range(2):
            self.run_cli("--system", "--dest", str(dest), "--link", str(links))
            link = links / base.THEME
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), dest / base.THEME)
            self.assertEqual(link.lstat().st_uid, 0)
            for version in ["3.0", "4.0"]:
                self.assertEqual(
                    (link / f"gtk-{version}/gtk.gresource").read_bytes(),
                    (base.ROOT / f"gtk-{version}/gtk.gresource").read_bytes(),
                )
        self.assertFalse(self.config.exists())
        self.run_cli("--system", "--dest", str(dest), "--link", str(links), "--remove")
        self.assertFalse(os.path.lexists(link))
        self.assertFalse((dest / base.THEME).exists())

    def test_shared_link_refuses_unrelated_real_directory(self):
        dest = self.base / "local/themes"
        links = self.base / "usr/themes"
        existing = links / base.THEME
        existing.mkdir(parents=True)
        marker = existing / "keep"
        marker.write_text("unrelated existing installation")
        self.run_cli(
            "--system", "--dest", str(dest), "--link", str(links), success=False
        )
        self.assertEqual(marker.read_text(), "unrelated existing installation")
        self.assertFalse(dest.exists())

    def test_shared_link_refuses_foreign_symlink(self):
        dest = self.base / "local/themes"
        links = self.base / "usr/themes"
        links.mkdir(parents=True)
        link = links / base.THEME
        other = self.base / "other"
        other.mkdir()
        link.symlink_to(other)
        self.run_cli(
            "--system", "--dest", str(dest), "--link", str(links), success=False
        )
        self.assertEqual(link.resolve(), other)
        self.assertFalse(dest.exists())

    def test_shared_link_requires_system_scope_and_different_parent(self):
        self.run_cli("--link", str(self.base / "links"), success=False)
        dest = self.base / "themes"
        self.run_cli(
            "--system", "--dest", str(dest), "--link", str(dest), success=False
        )
        self.assertFalse(dest.exists())

    def test_shared_link_dry_run_creates_no_parent_or_link(self):
        dest = self.base / "local/themes"
        links = self.base / "usr/themes"
        self.run_cli("--system", "--dest", str(dest), "--link", str(links), "--dry-run")
        self.assertFalse(dest.exists())
        self.assertFalse(links.exists())

    def test_shared_link_refuses_user_owned_or_writable_ancestors(self):
        self.assertEqual(os.geteuid(), 0)
        for problem in ["owner", "mode"]:
            with self.subTest(problem=problem):
                parent = self.base / problem
                parent.mkdir()
                if problem == "owner":
                    os.chown(parent, 1000, 1000)
                else:
                    parent.chmod(0o777)
                self.run_cli(
                    "--system",
                    "--dest",
                    str(parent / "themes"),
                    "--link",
                    str(self.base / "links"),
                    success=False,
                )
                self.assertFalse((parent / "themes").exists())

    def test_root_gtk3_application_loads_theme_through_shared_link(self):
        self.assertEqual(os.geteuid(), 0)
        dest = self.base / "sysroot/local/share/themes"
        links = self.base / "sysroot/usr/share/themes"
        env = dict(
            self.env,
            GTK_DATA_PREFIX=str(self.base / "sysroot/usr"),
            GSETTINGS_BACKEND="memory",
        )
        code = """import json, cairo, gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
Gtk.init([])
Gtk.Settings.get_default().set_property('gtk-theme-name', 'Adwaita-AMOLED')
w=Gtk.Window()
w.show_all()
while Gtk.events_pending(): Gtk.main_iteration()
s=cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
cr=cairo.Context(s)
cr.set_source_rgb(1, 0, 1); cr.paint()
Gtk.render_background(w.get_style_context(), cr, 0, 0, 4, 4)
s.flush(); b=bytes(s.get_data()); i=s.get_stride()+4
print(json.dumps([b[i+2], b[i+1], b[i], b[i+3]]))
w.destroy()
"""

        def probe():
            result = subprocess.run(
                [sys.executable, "-c", code],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout.splitlines()[-1])

        self.assertNotEqual(probe(), [0, 0, 0, 255])
        self.run_cli("--system", "--dest", str(dest), "--link", str(links))
        self.assertEqual(probe(), [0, 0, 0, 255])

    def test_shared_link_refuses_existing_user_owned_matching_link(self):
        self.assertEqual(os.geteuid(), 0)
        dest = self.base / "local/themes"
        links = self.base / "usr/themes"
        links.mkdir(parents=True)
        link = links / base.THEME
        link.symlink_to(dest / base.THEME)
        os.lchown(link, 1000, 1000)
        self.run_cli(
            "--system", "--dest", str(dest), "--link", str(links), success=False
        )
        self.assertFalse(dest.exists())
        self.assertEqual(link.lstat().st_uid, 1000)


if __name__ == "__main__":
    from report import main

    main()
