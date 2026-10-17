"""Native GNOME 46 Wayland regressions for the reported calendar/dash/switch defects."""

import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from test_shell import rules

ROOT = Path(__file__).resolve().parents[1]


class Shell46SourceTests(unittest.TestCase):
    def test_pinned_upstream_files_and_assets(self):
        theme = ROOT / "gnome-shell"
        metadata = json.loads((theme / "UPSTREAM-46.json").read_text())
        self.assertEqual(metadata["commit"], "49fa85b2fead489d5c1ce50ecaf28a114c831f1e")
        for name, record in metadata["files"].items():
            with self.subTest(path=name):
                self.assertEqual(
                    hashlib.sha256((theme / name).read_bytes()).hexdigest(),
                    record["sha256"],
                )

    def test_reproducible_css_and_preserved_upstream_geometry(self):
        theme = ROOT / "gnome-shell"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "theme.css"
            subprocess.run(
                ["bash", str(theme / "build.sh"), "--shell-version", "46", str(output)],
                check=True,
                capture_output=True,
            )
            self.assertEqual(
                output.read_bytes(), (theme / "gnome-shell-46.css").read_bytes()
            )
            compiled = output.read_text()
            stock = Path(temporary) / "stock.scss"
            stock.write_text(
                "$variant: 'dark';\n$contrast: 'normal';\n"
                + "\n".join(
                    f'@import "{theme / "sass/46/upstream" / name}";'
                    for name in ["colors", "drawing", "common", "widgets"]
                )
            )
            original = subprocess.run(
                ["sassc", "-t", "expanded", str(stock)],
                check=True,
                capture_output=True,
                text=True,
            )
        before, after = rules(original.stdout), rules(compiled)
        self.assertGreater(len(before), 800)
        self.assertGreaterEqual(len(after), len(before))
        colors = {
            "color",
            "background",
            "background-color",
            "background-image",
            "border",
            "border-color",
            "box-shadow",
            "-arrow-background-color",
            "-arrow-border-color",
            "-barlevel-overdrive-color",
            "warning-color",
        }
        for (selector, declarations), (new_selector, changed) in zip(before, after):
            self.assertEqual(selector, new_selector)
            self.assertEqual(
                [key for key, _ in declarations], [key for key, _ in changed]
            )
            for (key, value), (_, new_value) in zip(declarations, changed):
                if key not in colors and not key.endswith("-color"):
                    self.assertEqual(value, new_value, f"{selector}: {key}")
        for selector, declarations in after[len(before) :]:
            self.assertTrue(all(key in colors for key, _ in declarations), selector)


class Shell46Tests(unittest.TestCase):
    def test_real_shell_interactions(self):
        with tempfile.TemporaryDirectory(prefix="amoled-shell46-") as temporary:
            base = Path(temporary)
            output = Path(os.environ.get("THEME_TEST_OUTPUT", base / "evidence"))
            output.mkdir(parents=True, exist_ok=True)
            home = base / "home"
            home.mkdir()
            env = dict(
                os.environ,
                HOME=str(home),
                XDG_CONFIG_HOME=str(home / "config"),
                XDG_DATA_HOME=str(home / "data"),
                XDG_STATE_HOME=str(home / "state"),
                XDG_CACHE_HOME=str(home / "cache"),
                XDG_RUNTIME_DIR=str(base / "runtime"),
                THEME_TEST_ROOT=str(ROOT),
                THEME_TEST_OUTPUT=str(output),
                MUTTER_TESTS_DIR="/usr/share/mutter-14/tests",
                META_DBUS_RUNNER_DISABLE_LOGIND_PASSTHROUGH="1",
                GSETTINGS_BACKEND="keyfile",
                LIBGL_ALWAYS_SOFTWARE="1",
                XDG_CURRENT_DESKTOP="GNOME",
                XDG_SESSION_TYPE="wayland",
                GDK_BACKEND="wayland",
                GSK_RENDERER="cairo",
            )
            for key in ["DISPLAY", "SUDO_USER", "SUDO_UID", "GTK_THEME"]:
                env.pop(key, None)
            Path(env["XDG_RUNTIME_DIR"]).mkdir(mode=0o700)
            variant = os.environ.get("THEME_TEST_SHELL_VERSION", "auto")
            result = subprocess.run(
                [
                    str(ROOT / "install.sh"),
                    "install",
                    "--components",
                    "shell",
                    "--shell-version",
                    variant,
                    "--yes",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = home / "data/themes/Adwaita-AMOLED/gnome-shell/gnome-shell.css"
            self.assertEqual(
                installed.read_bytes(),
                (
                    ROOT
                    / f"gnome-shell/gnome-shell-{'46' if variant == 'auto' else variant}.css"
                ).read_bytes(),
            )
            extension = "amoled-interactions@test.local"
            directory = home / "data/gnome-shell/extensions" / extension
            directory.mkdir(parents=True)
            shutil.copyfile(
                ROOT / "tests/gnome-shell/interaction-extension.js",
                directory / "extension.js",
            )
            (directory / "metadata.json").write_text(
                json.dumps(
                    {
                        "uuid": extension,
                        "name": "Theme interaction test",
                        "description": "Isolated theme regression fixture",
                        "shell-version": ["46"],
                    }
                )
            )
            settings = [
                (
                    "org.gnome.shell",
                    "enabled-extensions",
                    repr(
                        [
                            "user-theme@gnome-shell-extensions.gcampax.github.com",
                            extension,
                        ]
                    ),
                ),
                ("org.gnome.shell", "disable-user-extensions", "false"),
                ("org.gnome.shell.extensions.user-theme", "name", "Adwaita-AMOLED"),
                ("org.gnome.desktop.interface", "color-scheme", "prefer-dark"),
                ("org.gnome.desktop.interface", "enable-animations", "false"),
                ("org.gnome.desktop.background", "picture-uri", "''"),
                ("org.gnome.desktop.background", "picture-uri-dark", "''"),
                ("org.gnome.shell", "favorite-apps", "['amoled-theme-test.desktop']"),
            ]
            applications = home / "data/applications"
            applications.mkdir(parents=True)
            (applications / "amoled-theme-test.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Theme test\nExec=/usr/bin/true\nIcon=system-file-manager\n"
            )
            for schema, key, value in settings:
                subprocess.run(
                    ["gsettings", "set", schema, key, value],
                    env=env,
                    check=True,
                    capture_output=True,
                )
            with (output / "shell46-session.log").open("w") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        str(ROOT / "tests/gnome-shell/dbus_runner.py"),
                        "--",
                        "bash",
                        str(ROOT / "tests/gnome-shell/session46.sh"),
                    ],
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    process.wait(timeout=90)
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
            log = (output / "shell46-session.log").read_text()
            report = output / "shell-interactions.json"
            self.assertTrue(report.is_file(), log)
            data = json.loads(report.read_text())
            self.assertNotIn("error", data, str(data) + "\n" + log)
            self.assertEqual(len(data["states"]), 6)
            self.assertNotRegex(
                log,
                r"Theme parsing error|Failed to parse stylesheet|Error loading.*assets/",
            )
            self.assertNotIn("Failed to load image", log)
            print(json.dumps(data))


if __name__ == "__main__":
    from report import main

    main()
