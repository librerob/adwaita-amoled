"""Bash desktop selection through real isolated preference backends."""

import os
import shutil
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


class DarkAppearanceTests(unittest.TestCase):
    """Opt-in appearance through real installed schemas and isolated keyfiles."""

    run_cli = base.InstallerTests.run_cli
    fake_program = base.InstallerTests.fake_program
    native = DesktopSettingTests.native

    GNOME = "org.gnome.desktop.interface"
    XAPP = "org.x.apps.portal"

    def setUp(self):
        base.InstallerTests.setUp(self)
        self.gsettings = shutil.which("gsettings")
        self.env.update(XDG_CURRENT_DESKTOP="GNOME", GSETTINGS_BACKEND="keyfile")
        for schema in [self.GNOME, self.XAPP]:
            self.native(
                ["gsettings", "set", schema, "color-scheme", "prefer-light"], self.env
            )

    def preference(self, schema):
        return self.native([self.gsettings, "get", schema, "color-scheme"], self.env)

    def test_opt_in_maps_desktops_without_selecting_theme(self):
        self.native(["gsettings", "set", self.GNOME, "gtk-theme", "Original"], self.env)
        for desktop in [
            "GNOME",
            "Budgie:GNOME",
            "X-Cinnamon:GNOME",
            "MATE:GNOME",
            "XFCE",
        ]:
            with self.subTest(desktop=desktop):
                for schema in [self.GNOME, self.XAPP]:
                    self.native(
                        ["gsettings", "set", schema, "color-scheme", "prefer-light"],
                        self.env,
                    )
                env = dict(self.env, XDG_CURRENT_DESKTOP=desktop)
                for _ in range(2):
                    self.run_cli("--prefer-dark", env=env)
                self.assertEqual(self.preference(self.GNOME), "'prefer-dark'")
                expected = (
                    "'prefer-light'"
                    if desktop in ["GNOME", "Budgie:GNOME"]
                    else "'prefer-dark'"
                )
                self.assertEqual(self.preference(self.XAPP), expected)
                self.assertEqual(
                    self.native(["gsettings", "get", self.GNOME, "gtk-theme"], env),
                    "'Original'",
                )

    def test_theme_activation_alone_preserves_preference(self):
        self.run_cli("--activate")
        for schema in [self.GNOME, self.XAPP]:
            self.assertEqual(self.preference(schema), "'prefer-light'")

    def test_dry_run_does_not_install_or_change_preferences(self):
        result = self.run_cli("--prefer-dark", "--dry-run")
        self.assertIn(
            "gsettings set org.gnome.desktop.interface color-scheme prefer-dark",
            result.stdout,
        )
        self.assertFalse(self.theme.exists())
        self.assertEqual(self.preference(self.GNOME), "'prefer-light'")

    def test_remove_keeps_preference_and_cannot_request_dark(self):
        self.run_cli("--prefer-dark")
        self.run_cli("--remove", "--prefer-dark", success=False)
        self.assertTrue(self.theme.is_dir())
        self.run_cli("--remove")
        self.assertFalse(self.theme.exists())
        self.assertEqual(self.preference(self.GNOME), "'prefer-dark'")

    def test_unknown_desktop_fails_before_installation(self):
        result = self.run_cli(
            "--prefer-dark",
            env=dict(self.env, XDG_CURRENT_DESKTOP="KDE"),
            success=False,
        )
        self.assertIn("Cannot configure dark appearance", result.stderr)
        self.assertFalse(self.theme.exists())
        self.assertEqual(self.preference(self.GNOME), "'prefer-light'")

    def test_locked_setting_rejected_before_replacing_existing_theme(self):
        self.run_cli()
        sentinel = self.theme / "untouched.txt"
        sentinel.write_text("existing installation\n")
        self.fake_program(
            "gsettings",
            'case $1 in range) printf "enum\\n\047prefer-dark\047\\n" ;; get) echo "\047prefer-light\047" ;; writable) echo false ;; *) exit 99 ;; esac',
        )
        result = self.run_cli("--prefer-dark", success=False)
        self.assertIn("setting is locked", result.stderr)
        self.assertEqual(sentinel.read_text(), "existing installation\n")
        self.assertEqual(self.preference(self.GNOME), "'prefer-light'")

    def test_cinnamon_with_only_gnome_key_uses_installed_fallback(self):
        real = self.native(["sh", "-c", "command -v gsettings"], self.env)
        self.fake_program(
            "gsettings",
            "[[ ${2:-} != org.x.apps.portal ]] || exit 1\nexec " + real + ' "$@"',
        )
        self.run_cli(
            "--prefer-dark", env=dict(self.env, XDG_CURRENT_DESKTOP="Cinnamon")
        )
        self.assertEqual(self.preference(self.GNOME), "'prefer-dark'")
        self.assertEqual(self.preference(self.XAPP), "'prefer-light'")

    def test_missing_or_incompatible_keys_rejected_without_copying(self):
        for body in ["exit 1", '[[ $1 != range ]] || echo "type s"']:
            self.fake_program("gsettings", body)
            self.run_cli("--prefer-dark", success=False)
            self.assertFalse(self.theme.exists())

    def test_cinnamon_with_only_xapp_key_uses_installed_fallback(self):
        real = self.gsettings
        self.fake_program(
            "gsettings",
            "[[ ${2:-} != org.gnome.desktop.interface ]] || exit 1\nexec "
            + real
            + ' "$@"',
        )
        self.run_cli(
            "--prefer-dark", env=dict(self.env, XDG_CURRENT_DESKTOP="Cinnamon")
        )
        self.assertEqual(self.preference(self.XAPP), "'prefer-dark'")
        self.assertEqual(self.preference(self.GNOME), "'prefer-light'")


if __name__ == "__main__":
    from report import main

    main()
