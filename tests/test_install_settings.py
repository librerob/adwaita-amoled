"""Bash desktop selection through real isolated preference backends."""

import os
import subprocess
import unittest
import test_installer as base


class DesktopSettingTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    fake_program = base.InstallerTests.fake_program

    def native(self, args, env):
        result = subprocess.run(
            args, env=env, text=True, capture_output=True, timeout=60
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def check_desktop(self, desktop, specifications):
        env = dict(self.env, XDG_CURRENT_DESKTOP=desktop, GSETTINGS_BACKEND="keyfile")
        self.run_cli("--activate", env=env)
        for schema, key in specifications:
            self.assertEqual(
                self.native(["gsettings", "get", schema, key], env), repr(base.THEME)
            )
        self.run_cli("--activate", env=env)
        self.run_cli("--remove", env=env)
        # Stateless removal deliberately leaves desktop preferences selected.
        for schema, key in specifications:
            self.assertEqual(
                self.native(["gsettings", "get", schema, key], env), repr(base.THEME)
            )

    def test_gnome_and_budgie_activation(self):
        for desktop in ["GNOME", "Budgie:GNOME"]:
            self.check_desktop(desktop, [("org.gnome.desktop.interface", "gtk-theme")])

    def test_cinnamon_activation(self):
        self.check_desktop(
            "X-Cinnamon",
            [
                ("org.cinnamon.desktop.interface", "gtk-theme"),
                ("org.cinnamon.desktop.wm.preferences", "theme"),
                ("org.cinnamon.theme", "name"),
            ],
        )

    def test_mate_activation(self):
        self.check_desktop(
            "MATE",
            [("org.mate.interface", "gtk-theme"), ("org.mate.Marco.general", "theme")],
        )

    def test_xfce_activation(self):
        self.assertIn(
            "DBUS_SESSION_BUS_ADDRESS", os.environ, "Run under dbus-run-session"
        )
        env = dict(self.env, XDG_CURRENT_DESKTOP="XFCE")
        self.native(
            [
                "dbus-update-activation-environment",
                "HOME",
                "XDG_CONFIG_HOME",
                "XDG_DATA_HOME",
                "XDG_CACHE_HOME",
            ],
            env,
        )
        query = ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"]
        self.native(query + ["--create", "-t", "string", "-s", "Original"], env)
        self.run_cli("--activate", env=env)
        self.assertEqual(self.native(query, env), base.THEME)
        self.run_cli("--remove", env=env)
        self.assertEqual(self.native(query, env), base.THEME)

    def test_shell_user_local_schema_and_enabled_extension_command(self):
        self.fake_program("gnome-shell", 'echo "GNOME Shell 46.0"')
        self.fake_program(
            "gnome-extensions", 'printf "%s\\n" "$*" >> "$TEST_EXTENSION_LOG"'
        )
        env = dict(
            self.env,
            XDG_CURRENT_DESKTOP="GNOME",
            GSETTINGS_BACKEND="keyfile",
            TEST_EXTENSION_LOG=str(self.base / "extension-log"),
        )
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
        self.native(
            ["gsettings", "set", "org.gnome.shell", "disable-user-extensions", "false"],
            env,
        )
        self.run_cli("--shell", "--activate", env=env)
        self.assertEqual(
            self.native(
                [
                    "gsettings",
                    "--schemadir",
                    str(schemas),
                    "get",
                    "org.gnome.shell.extensions.user-theme",
                    "name",
                ],
                env,
            ),
            repr(base.THEME),
        )
        self.assertIn("enable " + extension, (self.base / "extension-log").read_text())
        self.assertEqual(
            (self.theme / "gnome-shell/gnome-shell.css").read_bytes(),
            (base.ROOT / "gnome-shell/gnome-shell-46.css").read_bytes(),
        )


if __name__ == "__main__":
    from report import main

    main()
