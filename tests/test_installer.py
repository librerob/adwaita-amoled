"""User configuration preservation, transaction recovery and installer behavior."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "amoled_install", ROOT / "tools/install.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="amoled-installer-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "home with space # % ü"
        self.home.mkdir()
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            XDG_DATA_HOME=str(self.home / "data"),
            XDG_CONFIG_HOME=str(self.home / "config"),
            XDG_STATE_HOME=str(self.home / "state"),
            XDG_CACHE_HOME=str(self.home / "cache"),
            GSETTINGS_BACKEND="memory",
        )
        for name in [
            "SUDO_USER",
            "SUDO_UID",
            "ZDOTDIR",
            "NVIM_APPNAME",
            "BAT_CONFIG_PATH",
            "BAT_CACHE_PATH",
            "BAT_THEME",
            "KITTY_CONFIG_DIRECTORY",
            "GTK_THEME",
        ]:
            self.env.pop(name, None)
        self.env["XDG_CONFIG_DIRS"] = str(self.home / "empty-system-config")
        self.config = self.home / "config"
        self.data = self.home / "data"
        self.state = self.home / "state/adwaita-amoled/state.json"

    def run_cli(self, *args, success=True, env=None, root=ROOT):
        result = subprocess.run(
            [sys.executable, str(root / "tools/install.py"), *args],
            env=env or self.env,
            text=True,
            capture_output=True,
            timeout=90,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def install(self, selected="gtk,libadwaita", **kwargs):
        return self.run_cli(
            "install",
            "--components",
            selected,
            "--gtk4-mode",
            "legacy",
            "--yes",
            **kwargs,
        )

    def text(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode())

    def test_old_state_upgrade_and_failed_update_remain_undoable(self):
        self.text(
            self.state,
            json.dumps({"version": 1, "files": {}, "settings": {}, "options": {}}),
        )
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            plan = installer.Plan(store.roots, store.state)
            path = self.config / "fail"
            plan.put(path, b"new", "gtk")
            original = installer.atomic
            failed = False

            def fault(target, data, mode=0o600):
                nonlocal failed
                if target == path and not failed:
                    failed = True
                    raise OSError("simulated failure during old-state upgrade")
                return original(target, data, mode)

            with patch.object(installer, "atomic", side_effect=fault):
                with self.assertRaises(OSError):
                    store.transact(plan)
        self.assertEqual(json.loads(self.state.read_text())["version"], 1)
        self.install("gtk")
        self.assertEqual(json.loads(self.state.read_text())["version"], 2)
        self.run_cli("uninstall", "--yes")

    def test_dry_run_does_not_create_user_files(self):
        self.run_cli(
            "install",
            "--components",
            "gtk,libadwaita,kitty,nvim,rofi,zsh,qt,alacritty,wallpaper",
            "--gtk4-mode",
            "modern",
            "--dry-run",
        )
        self.assertEqual(list(self.home.iterdir()), [])

    def test_core_repeat_update_and_exact_undo(self):
        css = self.config / "gtk-4.0/gtk.css"
        self.text(css, "/* User rule */\r\n.custom { color: red; }\r\n")
        original = css.read_bytes()
        css.chmod(0o640)
        self.install()
        first = css.read_bytes()
        self.install()
        self.assertEqual(css.read_bytes(), first)
        self.run_cli("update", "--yes")
        self.assertEqual(css.read_bytes(), first)
        self.assertEqual(first.count(b"BEGIN Adwaita-AMOLED"), 1)
        self.assertIn(b"%20", first)
        self.assertIn(b"%23", first)
        self.assertIn(original, first)
        self.assertFalse((self.data / "themes/Adwaita-AMOLED/src").exists())
        for version in ["3.0", "4.0"]:
            self.assertEqual(
                (
                    self.data / f"themes/Adwaita-AMOLED/gtk-{version}/gtk.gresource"
                ).read_bytes(),
                (ROOT / f"gtk-{version}/gtk.gresource").read_bytes(),
            )
        self.run_cli("uninstall", "--yes")
        self.assertEqual(css.read_bytes(), original)
        self.assertEqual(css.stat().st_mode & 0o777, 0o640)
        self.assertEqual(json.loads(self.state.read_text())["files"], {})
        self.assertTrue(list((self.state.parent / "backups").glob("*.json")))
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)

    def test_known_manual_override_is_migrated_and_restored(self):
        css = self.config / "gtk-4.0/gtk.css"
        old = (ROOT / "extra/libadwaita/gtk.css").read_bytes()
        self.text(css, old.decode())
        self.install()
        self.assertNotIn(b"@define-color", css.read_bytes())
        self.run_cli("update", "--yes")
        self.assertNotIn(b"@define-color", css.read_bytes())
        css.write_bytes(css.read_bytes() + b"\n/* Later custom rule */\n")
        self.run_cli("update", "--yes")
        self.assertNotIn(b"@define-color", css.read_bytes())
        self.run_cli("uninstall", "--yes")
        self.assertEqual(css.read_bytes(), old + b"\n/* Later custom rule */\n")

    def test_custom_css_charset_and_later_changes_survive(self):
        css = self.config / "gtk-4.0/gtk.css"
        self.text(css, '@charset "UTF-8";\n.custom { color: #fff; }\n')
        self.install()
        self.assertTrue(css.read_text().startswith("@charset"))
        css.write_text(css.read_text() + ".later { color: #aaa; }\n")
        self.run_cli("update", "--yes")
        self.run_cli("uninstall", "--yes")
        self.assertEqual(
            css.read_text(),
            '@charset "UTF-8";\n.custom { color: #fff; }\n.later { color: #aaa; }\n',
        )

    def test_existing_leaf_symlink_target_is_not_modified(self):
        outside = self.base / "dotfiles.css"
        outside.write_text(".original {color: red;}\n")
        css = self.config / "gtk-4.0/gtk.css"
        css.parent.mkdir(parents=True)
        css.symlink_to(outside)
        self.install()
        self.assertFalse(css.is_symlink())
        self.assertEqual(outside.read_text(), ".original {color: red;}\n")
        self.run_cli("uninstall", "--yes")
        self.assertTrue(css.is_symlink())
        self.assertEqual(os.readlink(css), str(outside))

    def test_directory_symlink_and_relative_xdg_are_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.config.mkdir()
        (self.config / "gtk-4.0").symlink_to(outside, target_is_directory=True)
        self.install(success=False)
        self.assertEqual(list(outside.iterdir()), [])
        self.run_cli(
            "install",
            "--components",
            "gtk",
            "--yes",
            success=False,
            env=dict(self.env, XDG_DATA_HOME="relative"),
        )

    def test_local_runtime_edits_are_never_overwritten(self):
        self.install()
        css = self.data / "themes/Adwaita-AMOLED/cinnamon/cinnamon.css"
        css.write_text(css.read_text() + "\n/* user edit */\n")
        before = css.read_bytes()
        result = self.run_cli("update", "--yes", success=False)
        self.assertIn("local edits", result.stderr)
        self.assertEqual(css.read_bytes(), before)
        self.run_cli("uninstall", "--yes", success=False)
        self.assertEqual(css.read_bytes(), before)

    def test_changed_managed_block_is_a_conflict(self):
        self.install()
        css = self.config / "gtk-4.0/gtk.css"
        css.write_text(css.read_text().replace("gtk.css", "missing.css"))
        before = css.read_bytes()
        self.run_cli("update", "--yes", success=False)
        self.run_cli("uninstall", "--yes", success=False)
        self.assertEqual(css.read_bytes(), before)

    def test_preflight_invalid_toml_does_not_install_any_theme(self):
        self.text(self.config / "alacritty/alacritty.toml", "this is not TOML!!!")
        self.install("gtk,alacritty", success=False)
        self.assertFalse((self.data / "themes/Adwaita-AMOLED").exists())

    def test_alacritty_import_list_preserves_settings_and_undo(self):
        path = self.config / "alacritty/alacritty.toml"
        text = '# kept\n[general]\nimport = [\n  "old-theme.toml", # keep its semantics\n]\n[font]\nsize = 13\n'
        self.text(path, text)
        self.install("gtk,alacritty")
        import tomllib

        data = tomllib.loads(path.read_text())
        self.assertEqual(data["font"]["size"], 13)
        self.assertEqual(data["general"]["import"][0], "old-theme.toml")
        self.run_cli("update", "--yes")
        self.assertEqual(path.read_text().count("BEGIN Adwaita-AMOLED"), 1)
        path.write_text(path.read_text() + "\n[window]\nopacity=0.9\n")
        self.run_cli("uninstall", "--yes")
        self.assertEqual(path.read_text(), text + "\n[window]\nopacity=0.9\n")

    def test_new_alacritty_and_existing_empty_general(self):
        for text in ["", "[general]\nlive_config_reload=true\n[font]\nsize=12\n"]:
            path = self.config / "alacritty/alacritty.toml"
            self.text(path, text)
            self.install("alacritty")
            self.run_cli("uninstall", "--yes")
            self.assertEqual(path.read_text(), text)

    def test_extras_preserve_user_configs_and_custom_profile_locations(self):
        zdot = self.base / "external zsh"
        zdot.mkdir()
        env = dict(self.env, ZDOTDIR=str(zdot), NVIM_APPNAME="personal-nvim")
        paths = {
            self.config / "kitty/kitty.conf": "font_size 14\n",
            self.config / "personal-nvim/init.vim": "set number\n",
            self.config / "rofi/config.rasi": "configuration {show-icons: false;}\n",
            zdot / ".zshrc": "# plugins loaded here\n",
        }
        for path, text in paths.items():
            self.text(path, text)
        self.install("qt,kitty,nvim,rofi,zsh,wallpaper", env=env)
        for path, text in paths.items():
            self.assertTrue(path.read_text().startswith(text))
        self.assertTrue((self.config / "qt5ct/colors/Adwaita-AMOLED.conf").is_file())
        self.assertTrue(
            (self.config / "qt6ct/qss/fusion-simple-scrollbar.qss").is_file()
        )
        self.assertTrue(
            (self.data / "backgrounds/Adwaita-AMOLED/blackmount.png").is_file()
        )
        self.run_cli("uninstall", "--yes", env=env)
        for path, text in paths.items():
            self.assertEqual(path.read_text(), text)

    def test_alacritty_existing_fallback_is_preserved(self):
        path = self.home / ".alacritty.toml"
        self.text(path, "[font]\nsize=15\n")
        self.install("alacritty")
        self.assertIn("BEGIN Adwaita-AMOLED", path.read_text())
        self.assertFalse((self.config / "alacritty/alacritty.toml").exists())
        self.run_cli("uninstall", "--yes")
        self.assertEqual(path.read_text(), "[font]\nsize=15\n")

    def test_kitty_explicit_config_directory_is_preserved(self):
        directory = self.base / "external kitty"
        path = directory / "kitty.conf"
        self.text(path, "font_size 15\n")
        env = dict(self.env, KITTY_CONFIG_DIRECTORY=str(directory))
        self.install("kitty", env=env)
        self.assertIn("BEGIN Adwaita-AMOLED", path.read_text())
        self.assertFalse((self.config / "kitty/kitty.conf").exists())
        self.run_cli("uninstall", "--yes", env=env)
        self.assertEqual(path.read_text(), "font_size 15\n")

    def test_shell_variant_detection_upgrade_and_installed_copy(self):
        directory = self.base / "bin"
        directory.mkdir()
        executable = directory / "gnome-shell"
        executable.write_text("#!/bin/sh\nprintf 'GNOME Shell 46.10\\n'\n")
        executable.chmod(0o755)
        env = dict(self.env, PATH=str(directory) + os.pathsep + os.environ["PATH"])
        self.run_cli("install", "--components", "shell", "--yes", env=env)
        target = self.data / "themes/Adwaita-AMOLED"
        css = target / "gnome-shell/gnome-shell.css"
        self.assertEqual(
            css.read_bytes(), (ROOT / "gnome-shell/gnome-shell-46.css").read_bytes()
        )
        executable.write_text("#!/bin/sh\nprintf 'GNOME Shell 51.1\\n'\n")
        self.run_cli("update", "--yes", env=env, root=target)
        self.assertEqual(
            css.read_bytes(), (ROOT / "gnome-shell/gnome-shell-51.css").read_bytes()
        )
        self.run_cli("status", env=env, root=target)
        self.run_cli("uninstall", "--yes", env=env, root=target)
        self.assertFalse(css.exists())

    def test_unverified_shell_version_stops_explicit_shell_setup(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            installer.shutil, "which", return_value="gnome-shell"
        ), patch.object(installer, "command", return_value="GNOME Shell 47.0"):
            with self.assertRaisesRegex(
                installer.InstallError, "Unsupported Shell version"
            ):
                installer.shell_variant("auto", True)

    def test_dual_neovim_init_is_rejected_before_writes(self):
        self.text(self.config / "nvim/init.lua", "-- lua\n")
        self.text(self.config / "nvim/init.vim", '" vim\n')
        self.install("nvim", success=False)
        self.assertFalse((self.data / "themes").exists())

    def test_changes_after_plan_display_are_rejected(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            plan = installer.Plan(directories, store.state)
            path = self.config / "race.conf"
            self.text(path, "before")
            plan.put(path, b"planned", "kitty")
            path.write_text("later user edit")
            with self.assertRaises(installer.InstallError):
                store.transact(plan)
            self.assertEqual(path.read_text(), "later user edit")

    def test_transaction_failure_restores_earlier_files(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            plan = installer.Plan(directories, store.state)
            first, second = self.config / "first", self.config / "second"
            self.text(first, "old")
            plan.put(first, b"new", "kitty")
            plan.put(second, b"new", "kitty")
            original = installer.atomic
            failed = False

            def fault(path, data, mode=0o600):
                nonlocal failed
                if path == second and not failed:
                    failed = True
                    raise OSError("simulated disk error")
                return original(path, data, mode)

            with patch.object(installer, "atomic", side_effect=fault):
                with self.assertRaises(OSError):
                    store.transact(plan)
            self.assertEqual(first.read_text(), "old")
            self.assertFalse(second.exists())
            self.assertFalse(store.pending.exists())

    def test_interrupted_transaction_recovery(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            path = self.config / "interrupted"
            self.text(path, "before")
            before = installer.snapshot(path)
            installer.atomic(path, b"after", 0o644)
            journal = {
                "previous_state": store.state,
                "allowed": [str(p) for p in directories.values()],
                "changes": [
                    {
                        "kind": "file",
                        "path": str(path),
                        "before": before,
                        "after": installer.desired(b"after", 0o644),
                    }
                ],
            }
            installer.atomic(store.pending, json.dumps(journal).encode())
            store.recover()
            self.assertEqual(path.read_text(), "before")
            self.assertFalse(store.pending.exists())

    def test_unknown_desktop_activation_fails_before_user_files(self):
        self.install(
            "gtk", env=dict(self.env, XDG_CURRENT_DESKTOP="unknown"), success=True
        )
        # An explicit activation request must fail, not claim success after skipping it.
        self.run_cli(
            "install",
            "--components",
            "gtk",
            "--activate",
            "--yes",
            env=dict(self.env, XDG_CURRENT_DESKTOP="unknown"),
            success=False,
        )

    def test_uninstall_keeps_a_desktop_preference_changed_later(self):
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            store.state["settings"] = {
                "id": {
                    "id": "id",
                    "backend": "gsettings",
                    "schema": "example",
                    "key": "theme",
                    "component": "gtk",
                    "before": "'Old'",
                    "after": "'Adwaita-AMOLED'",
                }
            }
            with patch.object(installer, "setting_get", return_value="'Later choice'"):
                plan = installer.undo_plan(store)
            self.assertEqual(plan.settings, [])
            self.assertEqual(plan.forget_settings, {"id"})

    def test_extension_undo_preserves_other_extensions(self):
        with patch.dict(os.environ, self.env, clear=True):
            store = installer.Store(installer.roots())
            uuid = "user-theme@example"
            store.state["settings"] = {
                "id": {
                    "id": "id",
                    "backend": "gsettings",
                    "schema": "org.gnome.shell",
                    "key": "enabled-extensions",
                    "component": "shell",
                    "before": "['old@example']",
                    "after": repr(["old@example", uuid]),
                    "list_added": [uuid],
                    "list_removed": [],
                }
            }
            with patch.object(
                installer,
                "setting_get",
                return_value=repr(["old@example", uuid, "new@example"]),
            ):
                plan = installer.undo_plan(store)
            self.assertEqual(
                installer.string_array(plan.settings[0]["after"]),
                ["old@example", "new@example"],
            )

    def test_legacy_theme_directory_cannot_shadow_installation(self):
        legacy = self.home / ".themes/Adwaita-AMOLED"
        legacy.mkdir(parents=True)
        self.text(legacy / "keep.txt", "old checkout")
        self.install(success=False)
        self.assertEqual((legacy / "keep.txt").read_text(), "old checkout")
        self.assertFalse((self.data / "themes/Adwaita-AMOLED").exists())

    def test_symlinked_backup_directory_is_rejected_before_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        backup = self.state.parent / "backups"
        backup.parent.mkdir(parents=True)
        backup.symlink_to(outside, target_is_directory=True)
        self.install(success=False)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.data / "themes/Adwaita-AMOLED").exists())

    def test_directory_replaced_after_planning_is_rejected(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            plan = installer.Plan(directories, store.state)
            directory = self.config / "kitty"
            directory.mkdir(parents=True)
            plan.put(directory / "kitty.conf", b"planned", "kitty")
            directory.rmdir()
            outside = self.base / "outside"
            outside.mkdir()
            directory.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(installer.InstallError):
                store.transact(plan)
            self.assertEqual(list(outside.iterdir()), [])

    def test_bat_cache_failure_rolls_back_installed_files(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            plan = installer.Plan(directories, store.state)
            path = self.config / "bat/config"
            self.text(path, "original")
            plan.put(path, b"new", "bat")
            plan.bat = ("bat", directories["cache"])
            with patch.object(
                installer, "command", side_effect=installer.InstallError("cache failed")
            ):
                with self.assertRaises(installer.InstallError):
                    store.transact(plan)
            self.assertEqual(path.read_text(), "original")
            self.assertFalse(store.pending.exists())

    def test_desktop_failure_rolls_back_files_and_earlier_preferences(self):
        with patch.dict(os.environ, self.env, clear=True):
            directories = installer.roots()
            store = installer.Store(directories)
            plan = installer.Plan(directories, store.state)
            values = {"one": "'Old'", "two": "'Old'"}
            failed = False

            def get(spec):
                return values[spec["key"]]

            def set_value(spec, value):
                nonlocal failed
                if spec["key"] == "two" and not failed:
                    failed = True
                    raise installer.InstallError("read-only desktop preference")
                values[spec["key"]] = value

            with patch.object(installer, "setting_get", side_effect=get), patch.object(
                installer, "setting_set", side_effect=set_value
            ):
                plan.put(self.config / "new", b"new", "gtk")
                for key in ["one", "two"]:
                    plan.add_setting(
                        "gsettings", "example", key, installer.THEME, "gtk"
                    )
                with self.assertRaises(installer.InstallError):
                    store.transact(plan)
            self.assertEqual(values, {"one": "'Old'", "two": "'Old'"})
            self.assertFalse((self.config / "new").exists())

    def test_release_layout_needs_no_sources_or_compiler(self):
        import tarfile

        archive = self.base / "preview.tar.gz"
        subprocess.run(
            [sys.executable, str(ROOT / "tools/package.py"), str(archive)],
            check=True,
            capture_output=True,
        )
        first = archive.read_bytes()
        subprocess.run(
            [sys.executable, str(ROOT / "tools/package.py"), str(archive)],
            check=True,
            capture_output=True,
        )
        self.assertEqual(archive.read_bytes(), first)
        release = self.base / "unpacked"
        with tarfile.open(archive) as package:
            for member in package.getmembers():
                self.assertTrue(member.isfile())
                self.assertFalse(Path(member.name).is_absolute())
                self.assertNotIn("..", Path(member.name).parts)
                path = release / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(package.extractfile(member).read())
                path.chmod(member.mode)
        theme = release / installer.THEME
        self.assertFalse((theme / "src").exists())
        self.run_cli(
            "install",
            "--components",
            "gtk,libadwaita",
            "--gtk4-mode",
            "legacy",
            "--yes",
            root=theme,
        )
        self.assertTrue((self.config / "gtk-4.0/gtk.css").is_file())
        self.run_cli("uninstall", "--yes", root=theme)
        result = subprocess.run(
            [
                "bash",
                str(theme / "install.sh"),
                "install",
                "--components",
                "gtk",
                "--yes",
            ],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    from report import main

    main()
