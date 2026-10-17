"""Real Flatpak override parsing with declared app/runtime metadata fixtures.

These cases exercise permission/configuration preservation; the separate native
sandbox fixture verifies actual installed app/runtime discovery and CSS loading.
"""

import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_installer as base

installer = base.installer
support = installer.sandbox


class FlatpakInstallerTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    text = base.InstallerTests.text

    def setup_app(self, version=(4, 14, 5)):
        self.executable = shutil.which("flatpak")
        self.assertIsNotNone(self.executable, "Install Flatpak for these checks.")
        self.app = "org.example.AmoledTest"
        self.app_location = self.base / "app-install"
        self.runtime_location = self.base / "runtime-install"
        if version:
            major, minor, micro = version
            age, interface = (
                (100 * minor + micro, 0) if minor % 2 else (100 * minor, micro)
            )
            library = (
                self.runtime_location / f"files/lib/libgtk-4.so.1.{age}.{interface}"
            )
            library.parent.mkdir(parents=True)
            library.write_bytes(b"\x7fELF" + b"\0" * 12)
        self.user_dir = self.home / "external flatpak user dir"
        self.env["FLATPAK_USER_DIR"] = str(self.user_dir)
        self.override = self.user_dir / "overrides" / self.app
        self.css = self.home / ".var/app" / self.app / "config/gtk-4.0/gtk.css"
        self.effective = ""
        self.original_command = installer.command

    def metadata(self, args, env=None):
        if len(args) > 1 and args[1] == "info":
            if "--show-permissions" in args:
                return self.effective
            if "--show-runtime" in args:
                return "org.example.Platform/x86_64/test"
            if "--show-location" in args:
                return str(
                    self.runtime_location
                    if args[-1].startswith("runtime/")
                    else self.app_location
                )
        return self.original_command(args, env=env)

    def plan(self, store, mode="auto"):
        plan = installer.Plan(store.roots, store.state)
        target = store.roots["data"] / "themes/Adwaita-AMOLED"
        with patch.object(installer, "command", side_effect=self.metadata):
            support.configure(installer.__dict__, plan, target, {self.app: mode})
        return plan

    def test_auto_uses_flatpak_library_and_exact_undo(self):
        self.setup_app()
        original = (
            "[Context]\nfilesystems=xdg-download:ro;\n[Environment]\nMY_SETTING=keep\n"
        )
        self.text(self.override, original)
        self.text(self.css, "/* custom app css */\n")
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            store.transact(self.plan(store))
            self.assertIn("/extra/libadwaita/gtk.css", self.css.read_text())
            self.assertNotIn("gtk-modern.css", self.css.read_text())
            with support.KeyFile(self.override.read_text()) as k:
                permissions = k.filesystems()
                self.assertEqual(k.string("Environment", "MY_SETTING"), "keep")
            self.assertIn("xdg-download:ro", permissions)
            self.assertTrue(all(p.endswith(":ro") for p in permissions))
            self.assertEqual(len(permissions), 3)
            self.assertIsNone(
                support.KeyFile(self.override.read_text()).string(
                    "Environment", "GTK_THEME"
                )
            )
            store.transact(self.plan(store))
            store.transact(installer.undo_plan(store), uninstall=True)
            self.assertEqual(self.override.read_text(), original)
            self.assertEqual(self.css.read_text(), "/* custom app css */\n")

    def test_later_real_flatpak_edits_survive_update_and_undo(self):
        self.setup_app((4, 24, 1))
        self.text(self.override, "[Context]\nfilesystems=xdg-download:ro;\n")
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            store.transact(self.plan(store))
            installer.command(
                [
                    self.executable,
                    "override",
                    "--user",
                    "--filesystem=xdg-music:ro",
                    "--env=MY_LATER_SETTING=yes",
                    self.app,
                ]
            )
            self.css.write_text(self.css.read_text() + "/* later user rule */\n")
            store.transact(self.plan(store))
            store.transact(installer.undo_plan(store), uninstall=True)
            with support.KeyFile(self.override.read_text()) as k:
                self.assertEqual(
                    set(k.filesystems()), {"xdg-download:ro", "xdg-music:ro"}
                )
                self.assertEqual(k.string("Environment", "MY_LATER_SETTING"), "yes")
            self.assertEqual(self.css.read_text(), "/* later user rule */\n")

    def test_changed_theme_permission_is_kept_as_a_conflict(self):
        self.setup_app()
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            store.transact(self.plan(store))
            installer.command(
                [
                    self.executable,
                    "override",
                    "--user",
                    "--filesystem=xdg-data/themes/Adwaita-AMOLED",
                    self.app,
                ]
            )
            before = self.override.read_bytes()
            with self.assertRaises(installer.InstallError):
                self.plan(store)
            with self.assertRaises(installer.InstallError):
                installer.undo_plan(store)
            self.assertEqual(self.override.read_bytes(), before)

    def test_host_config_sharing_and_custom_config_home_are_rejected(self):
        self.setup_app()
        for text in [
            "[Context]\nfilesystems=xdg-config/gtk-4.0:ro;\n",
            "[Environment]\nXDG_CONFIG_HOME=/custom/config\n",
        ]:
            self.effective = text
            with patch.dict(os.environ, self.env, clear=True):
                store = installer.Store(installer.roots())
                with self.assertRaises(installer.InstallError):
                    self.plan(store)
                self.assertFalse(self.css.exists())
                self.assertFalse(self.override.exists())

    def test_incompatible_modern_mode_is_rejected(self):
        self.setup_app()
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            with self.assertRaises(installer.InstallError):
                self.plan(store, "modern")
            self.assertFalse(self.css.exists())

    def test_unknown_library_needs_explicit_choice(self):
        self.setup_app(None)
        library = self.runtime_location / "files/lib/libgtk-4.so.1"
        library.parent.mkdir(parents=True)
        library.write_bytes(b"\x7fELF")
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            with self.assertRaises(installer.InstallError):
                self.plan(store)
            store.transact(self.plan(store, "modern"))
            self.assertIn("gtk-modern.css", self.css.read_text())

    def test_gtk3_only_does_not_add_gtk4_override(self):
        self.setup_app(None)
        library = self.runtime_location / "files/lib/libgtk-3.so.0"
        library.parent.mkdir(parents=True)
        library.write_bytes(b"\x7fELF")
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            store.transact(self.plan(store))
            self.assertFalse(self.css.exists())
            path = self.css.parent.parent / "gtk-3.0/settings.ini"
            with support.KeyFile(path.read_text()) as k:
                self.assertEqual(
                    k.string("Settings", "gtk-theme-name"), "Adwaita-AMOLED"
                )

    def test_real_parser_handles_spaces_semicolons_and_colons(self):
        self.setup_app()
        with patch.dict(os.environ, self.env, clear=True):
            values = support.canonical_grants(
                installer.__dict__,
                self.executable,
                self.app,
                [str(self.home / "theme ; : # ü")],
            )
            self.assertEqual(len(values), 1)
            text = support.render_filesystems("# retained\n", values)
            with support.KeyFile(text) as k:
                self.assertEqual(k.filesystems(), values)
            self.assertTrue(text.startswith("# retained"))

    def test_selective_undo_keeps_native_and_other_apps(self):
        self.setup_app((4, 24, 1))
        other = "org.example.OtherApp"
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            plan = installer.Plan(store.roots, store.state)
            target = store.roots["data"] / "themes/Adwaita-AMOLED"
            native = self.config / "native-test"
            plan.put(native, b"native kept", "theme")
            with patch.object(installer, "command", side_effect=self.metadata):
                support.configure(
                    installer.__dict__, plan, target, {self.app: "auto", other: "auto"}
                )
            store.transact(plan)
            store.transact(
                installer.undo_plan(store, flatpaks={self.app}), uninstall=True
            )
            self.assertEqual(native.read_bytes(), b"native kept")
            self.assertFalse(self.css.exists())
            self.assertTrue(
                (self.home / ".var/app" / other / "config/gtk-4.0/gtk.css").exists()
            )
            self.assertIn(
                "Adwaita-AMOLED", (self.user_dir / "overrides" / other).read_text()
            )

    def test_failure_restores_override_and_app_configuration(self):
        self.setup_app()
        original = "[Environment]\nKEEP=yes\n"
        self.text(self.override, original)
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            plan = self.plan(store)
            original_atomic = installer.atomic
            failed = False

            def fault(path, data, mode=0o600):
                nonlocal failed
                if path == self.css and not failed:
                    failed = True
                    raise OSError("simulated write failure")
                return original_atomic(path, data, mode)

            with patch.object(installer, "atomic", side_effect=fault):
                with self.assertRaises(OSError):
                    store.transact(plan)
            self.assertEqual(self.override.read_text(), original)
            self.assertFalse(self.css.exists())

    def test_invalid_app_ids_and_modes_cannot_escape_directories(self):
        for value in [
            "../../App",
            "org.example.App/../../etc",
            "org.example.App=bad",
            "org.example.App\n",
        ]:
            with self.assertRaises(installer.InstallError):
                support.selections([value], {}, installer.InstallError)
        self.assertEqual(
            support.selections(["org.example.App=legacy"], {}, installer.InstallError),
            {"org.example.App": "legacy"},
        )


if __name__ == "__main__":
    from report import main

    main()
