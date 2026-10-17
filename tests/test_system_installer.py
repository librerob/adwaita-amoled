"""Root-owned system staging, directory readability and independent undo."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_installer as base

installer = base.installer
ROOT = base.ROOT


class SystemInstallerTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(
            os.geteuid(), 0, "Run this suite as root; all writes are staged under /tmp."
        )
        self.temp = tempfile.TemporaryDirectory(prefix="amoled-system-stage-")
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name)
        self.env = dict(
            os.environ,
            HOME=str(self.stage / "calling-user"),
            XDG_DATA_HOME=str(self.stage / "caller-data"),
            XDG_CONFIG_HOME=str(self.stage / "caller-config"),
            XDG_STATE_HOME=str(self.stage / "caller-state"),
            SUDO_USER="calling-user",
        )
        self.target = self.stage / "usr/local/share/themes/Adwaita-AMOLED"
        self.state = self.stage / "var/lib/adwaita-amoled/state.json"
        self.root_home = self.stage / installer.pwd.getpwuid(0).pw_dir.lstrip("/")

    def cli(self, action, *args, success=True):
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools/install.py"),
                action,
                "--system",
                "--system-root",
                str(self.stage),
                *args,
            ],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_root_owned_readable_runtime_and_repeatable_undo(self):
        self.cli("install", "--yes")
        self.cli("update", "--yes")
        self.cli("status")
        for path in [self.target, *self.target.rglob("*")]:
            self.assertEqual(path.stat().st_uid, 0, str(path))
            self.assertEqual(path.stat().st_gid, 0, str(path))
            self.assertEqual(
                path.stat().st_mode & 0o777,
                (
                    0o755
                    if path.is_dir()
                    or (ROOT / path.relative_to(self.target)).stat().st_mode & 0o111
                    else 0o644
                ),
                str(path),
            )
        for path in self.stage.glob("caller-*"):
            self.assertFalse(path.exists())
        self.assertFalse((self.root_home / ".config/gtk-4.0/gtk.css").exists())
        for v in ["3.0", "4.0"]:
            self.assertEqual(
                (self.target / f"gtk-{v}/gtk.gresource").read_bytes(),
                (ROOT / f"gtk-{v}/gtk.gresource").read_bytes(),
            )
        self.cli("uninstall", "--yes")
        self.assertFalse((self.target / "index.theme").exists())
        self.assertEqual(json.loads(self.state.read_text())["files"], {})

    def test_original_owner_modes_and_bytes_are_restored(self):
        path = self.target / "gtk-3.0/gtk.css"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"old theme")
        path.chmod(0o600)
        os.chown(path, 65534, 65534)
        path.parent.chmod(0o700)
        os.chown(path.parent, 65534, 65534)
        self.cli("install", "--yes")
        self.assertEqual(path.stat().st_uid, 0)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o755)
        self.cli("uninstall", "--yes")
        self.assertEqual(path.read_bytes(), b"old theme")
        self.assertEqual(path.stat().st_uid, 65534)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_uid, 65534)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_explicit_root_gtk4_uses_root_home_and_undo(self):
        path = self.root_home / ".config/gtk-4.0/gtk.css"
        path.parent.mkdir(parents=True)
        path.write_text("/* root custom */\n")
        self.cli("install", "--root-gtk4", "--yes")
        self.assertIn("BEGIN Adwaita-AMOLED", path.read_text())
        self.assertIn("root custom", path.read_text())
        self.assertIn(self.target.as_uri(), path.read_text())
        native_env = dict(
            self.env,
            HOME=str(self.root_home),
            XDG_CONFIG_HOME=str(self.root_home / ".config"),
            XDG_DATA_HOME=str(self.stage / "usr/local/share"),
            XDG_CACHE_HOME=str(self.stage / "var/cache"),
            GSETTINGS_BACKEND="memory",
            GSK_RENDERER="cairo",
        )
        for key in ["GTK_THEME", "GTK_PATH", "GTK_DATA_PREFIX"]:
            native_env.pop(key, None)
        for scheme in [[], ["--light"]]:
            result = subprocess.run(
                ["python3", str(ROOT / "tests/installed_gtk4.py"), *scheme],
                env=native_env,
                text=True,
                capture_output=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["automatic_user_css"])
        self.cli("uninstall", "--yes")
        self.assertEqual(path.read_text(), "/* root custom */\n")

    def test_dry_run_and_invalid_mixed_scopes_leave_stage_empty(self):
        self.cli("install", "--dry-run")
        self.assertEqual(list(self.stage.iterdir()), [])
        self.cli("install", "--flatpak", "org.example.App", "--yes", success=False)
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_user_owned_system_state_is_not_trusted(self):
        self.state.parent.mkdir(parents=True)
        self.state.write_text('{"version":2,"files":{},"settings":{},"options":{}}')
        os.chown(self.state, 65534, 65534)
        result = self.cli("install", "--yes", success=False)
        self.assertIn("must be root-owned", result.stderr)
        self.assertFalse(self.target.exists())

    def test_failure_restores_owner_modes_and_bytes(self):
        directories = installer.system_roots(str(self.stage))
        store = installer.Store(directories)
        plan = installer.Plan(directories, store.state, system=True)
        plan.directory_roots.append(self.target)
        first = self.target / "first"
        second = self.target / "second"
        first.parent.mkdir(parents=True)
        first.write_bytes(b"original")
        first.chmod(0o600)
        os.chown(first, 65534, 65534)
        first.parent.chmod(0o700)
        os.chown(first.parent, 65534, 65534)
        plan.put(first, b"changed", "theme", mode=0o644)
        plan.put(second, b"new", "theme", mode=0o644)
        original = installer.atomic
        failed = False

        def fault(path, data, mode=0o600):
            nonlocal failed
            if path == second and not failed:
                failed = True
                raise OSError("simulated disk failure")
            return original(path, data, mode)

        with patch.object(installer, "atomic", side_effect=fault):
            with self.assertRaises(OSError):
                store.transact(plan)
        self.assertEqual(first.read_bytes(), b"original")
        self.assertEqual(first.stat().st_uid, 65534)
        self.assertEqual(first.parent.stat().st_uid, 65534)
        self.assertEqual(first.parent.stat().st_mode & 0o777, 0o700)
        self.assertFalse(second.exists())

    def test_existing_symlinked_directory_is_not_followed(self):
        outside = self.stage / "outside"
        outside.mkdir()
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(outside, target_is_directory=True)
        self.cli("install", "--yes", success=False)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    from report import main

    main()
