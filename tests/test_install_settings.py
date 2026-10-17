"""Actual desktop preference backends in isolated users; XFCE needs dbus-run-session."""

import os
import subprocess
import unittest
from unittest.mock import patch

import test_installer as base

installer = base.installer


class DesktopSettingTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli

    # Reuse isolated HOME/CLI helpers without inheriting the unit-test cases.
    def check_desktop(self, desktop, specifications):
        env = dict(self.env, XDG_CURRENT_DESKTOP=desktop, GSETTINGS_BACKEND="keyfile")

        def get(schema, key):
            return subprocess.check_output(
                ["gsettings", "get", schema, key], env=env, text=True
            ).strip()

        original = {(schema, key): get(schema, key) for schema, key in specifications}
        self.run_cli("install", "--components", "gtk", "--activate", "--yes", env=env)
        for schema, key in specifications:
            self.assertEqual(get(schema, key), repr(installer.THEME))
        self.run_cli("update", "--yes", env=env)
        self.run_cli("uninstall", "--yes", env=env)
        for (schema, key), before in original.items():
            self.assertEqual(get(schema, key), before)

    def test_gnome_and_budgie_activation_and_undo(self):
        for desktop in ["GNOME", "Budgie:GNOME"]:
            with self.subTest(desktop=desktop):
                self.check_desktop(
                    desktop, [("org.gnome.desktop.interface", "gtk-theme")]
                )

    def test_cinnamon_activation_and_undo(self):
        self.check_desktop(
            "X-Cinnamon",
            [
                ("org.cinnamon.desktop.interface", "gtk-theme"),
                ("org.cinnamon.desktop.wm.preferences", "theme"),
                ("org.cinnamon.theme", "name"),
            ],
        )

    def test_mate_activation_and_undo(self):
        self.check_desktop(
            "MATE",
            [("org.mate.interface", "gtk-theme"), ("org.mate.Marco.general", "theme")],
        )

    def test_xfce_activation_and_undo(self):
        self.assertIn(
            "DBUS_SESSION_BUS_ADDRESS",
            os.environ,
            "Run this case under dbus-run-session",
        )
        env = dict(self.env, XDG_CURRENT_DESKTOP="XFCE")
        subprocess.run(
            [
                "dbus-update-activation-environment",
                "HOME",
                "XDG_CONFIG_HOME",
                "XDG_DATA_HOME",
                "XDG_CACHE_HOME",
            ],
            env=env,
            check=True,
            capture_output=True,
        )
        query = ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"]
        subprocess.run(
            query + ["--create", "-t", "string", "-s", "Original"],
            env=env,
            check=True,
            capture_output=True,
        )
        self.run_cli("install", "--components", "gtk", "--activate", "--yes", env=env)
        self.assertEqual(
            subprocess.check_output(query, env=env, text=True).strip(), installer.THEME
        )
        self.run_cli("uninstall", "--yes", env=env)
        self.assertEqual(
            subprocess.check_output(query, env=env, text=True).strip(), "Original"
        )

    def test_user_local_shell_schema_and_extension_membership_undo(self):
        env = dict(self.env, XDG_CURRENT_DESKTOP="GNOME", GSETTINGS_BACKEND="keyfile")
        extension = "user-theme@gnome-shell-extensions.gcampax.github.com"
        schemas = self.data / "gnome-shell/extensions" / extension / "schemas"
        schemas.mkdir(parents=True)
        (schemas / "org.gnome.shell.extensions.user-theme.gschema.xml").write_text(
            """<schemalist>
          <schema id="org.gnome.shell.extensions.user-theme" path="/org/gnome/shell/extensions/user-theme/">
            <key name="name" type="s"><default>''</default></key>
          </schema></schemalist>"""
        )
        subprocess.run(["glib-compile-schemas", str(schemas)], check=True)
        with patch.dict(os.environ, env, clear=True):
            disabled_spec = {
                "backend": "gsettings",
                "schema": "org.gnome.shell",
                "key": "disabled-extensions",
            }
            installer.setting_set(disabled_spec, repr([extension]))
            store = installer.Store(installer.roots())
            plan = installer.Plan(store.roots, store.state)
            native_command = installer.command

            def metadata(args, env=None):
                if args == ["gnome-shell", "--version"]:
                    return "GNOME Shell 51.1"
                if args == ["gnome-extensions", "list"]:
                    return extension
                if args == ["gsettings", "list-schemas"]:
                    return "\n".join(
                        x
                        for x in native_command(args).splitlines()
                        if x != "org.gnome.shell.extensions.user-theme"
                    )
                return native_command(args, env=env)

            # Only session metadata is simulated; actual GSettings reads/writes and local schema loading are used.
            with patch.object(installer, "command", side_effect=metadata):
                installer.activation(plan, {"shell"}, True, "GNOME")
                store.transact(plan)
            record = next(
                x for x in store.state["settings"].values() if x["key"] == "name"
            )
            self.assertEqual(record["schema_dir"], str(schemas))
            self.assertEqual(installer.setting_get(record), repr(installer.THEME))
            enabled = next(
                x
                for x in store.state["settings"].values()
                if x["key"] == "enabled-extensions"
            )
            values = installer.string_array(installer.setting_get(enabled))
            self.assertIn(extension, values)
            installer.setting_set(enabled, repr(values + ["later@example"]))
            store.transact(installer.undo_plan(store), uninstall=True)
            self.assertNotIn(
                extension, installer.string_array(installer.setting_get(enabled))
            )
            self.assertIn(
                "later@example", installer.string_array(installer.setting_get(enabled))
            )
            self.assertEqual(installer.setting_get(record), "''")
            self.assertEqual(
                installer.string_array(installer.setting_get(disabled_spec)),
                [extension],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
