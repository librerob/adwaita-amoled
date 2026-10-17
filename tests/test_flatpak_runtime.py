"""Build/sign/install a local Flatpak runtime and test actual sandbox CSS loading.

No remote runtime or application download is used. Requires root, Xvfb/D-Bus,
Flatpak, gcc, GTK4/libadwaita development files, pax-utils and GnuPG. All Flatpak,
GPG and HOME data is temporary. --prepare-only validates repository/install/undo
without starting a sandbox; it is for restricted local environments, never CI.
"""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREPARE_ONLY = "--prepare-only" in sys.argv
if PREPARE_ONLY:
    sys.argv.remove("--prepare-only")


def command(args, env, timeout=120):
    result = subprocess.run(
        args, env=env, text=True, capture_output=True, timeout=timeout
    )
    if result.returncode:
        raise AssertionError(
            "Command failed: "
            + shlex.join(map(str, args))
            + "\n"
            + result.stdout
            + result.stderr
        )
    return result.stdout.strip()


def copy_library(path, files):
    path = Path(path)
    # Flatpak maps /lib* onto /usr/lib*. Preserve every dependency's SONAME link.
    name = (
        path.relative_to("/usr")
        if path.is_relative_to("/usr")
        else path.relative_to("/")
    )
    target = files / name
    target.parent.mkdir(parents=True, exist_ok=True)
    real = path.resolve()
    if path.is_symlink():
        real_target = target.parent / real.name
        if not real_target.exists():
            shutil.copy2(real, real_target)
        if not target.exists():
            target.symlink_to(real.name)
    elif not target.exists():
        shutil.copy2(path, target)


class FlatpakRuntimeTests(unittest.TestCase):
    def test_signed_local_runtime_before_install_after_install_and_undo(self):
        self.assertEqual(
            os.geteuid(),
            0,
            "Run as root in an isolated CI/test environment; writes stay in temporary directories.",
        )
        self.assertFalse(
            PREPARE_ONLY and os.environ.get("GITHUB_ACTIONS") == "true",
            "CI must exercise the actual sandbox.",
        )
        with tempfile.TemporaryDirectory(prefix="amoled-real-flatpak-") as temporary:
            base = Path(temporary)
            home = base / "home # ü"
            home.mkdir()
            env = dict(
                os.environ,
                HOME=str(home),
                XDG_DATA_HOME=str(home / "data"),
                XDG_CONFIG_HOME=str(home / "config"),
                XDG_STATE_HOME=str(home / "state"),
                XDG_CACHE_HOME=str(home / "cache"),
                FLATPAK_USER_DIR=str(home / "data/flatpak"),
                GNUPGHOME=str(base / "gpg"),
                GSETTINGS_BACKEND="memory",
                GSK_RENDERER="cairo",
            )
            for name in ["SUDO_USER", "GTK_THEME", "GTK_PATH", "GTK_DATA_PREFIX"]:
                env.pop(name, None)
            Path(env["GNUPGHOME"]).mkdir(mode=0o700)
            runtime = base / "runtime"
            files = runtime / "usr"
            files.mkdir(parents=True)
            (runtime / "files").mkdir()
            app = base / "app"
            binary = app / "files/bin/amoled-probe"
            binary.parent.mkdir(parents=True)
            flags = shlex.split(
                command(
                    ["pkg-config", "--cflags", "--libs", "gtk4", "libadwaita-1"], env
                )
            )
            command(
                ["gcc", str(ROOT / "tests/flatpak_probe.c"), "-o", str(binary), *flags],
                env,
            )
            dependencies = command(
                ["/usr/bin/python3", "/usr/bin/lddtree", "-l", str(binary)], env
            ).splitlines()
            for name in dependencies:
                if Path(name).resolve() != binary.resolve():
                    copy_library(name, files)
            # Pango text rendering needs a runtime-owned font and fontconfig setup.
            font = next(iter(Path("/usr/share/fonts").rglob("DejaVuSans.ttf")), None)
            if font is None:
                raise AssertionError(
                    "Install fonts-dejavu-core for the sandbox fixture."
                )
            font_target = files / "share/fonts/DejaVuSans.ttf"
            font_target.parent.mkdir(parents=True)
            shutil.copy2(font, font_target)
            font_config = files / "etc/fonts/fonts.conf"
            font_config.parent.mkdir(parents=True)
            font_config.write_text(
                '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><cachedir>/tmp/fontconfig-cache</cachedir></fontconfig>'
            )
            schemas = Path("/usr/share/glib-2.0/schemas/gschemas.compiled")
            target = files / "share/glib-2.0/schemas/gschemas.compiled"
            target.parent.mkdir(parents=True)
            shutil.copy2(schemas, target)
            arch = command(["flatpak", "--default-arch"], env)
            runtime_name = "org.example.AmoledTest.Platform"
            app_name = "org.example.AmoledTest.App"
            branch = "test"
            ref = f"{runtime_name}/{arch}/{branch}"
            (runtime / "metadata").write_text(
                f"[Runtime]\nname={runtime_name}\nruntime={ref}\nsdk={ref}\n"
            )
            (app / "metadata").write_text(
                f"[Application]\nname={app_name}\nruntime={ref}\nsdk={ref}\ncommand=amoled-probe\n[Context]\nshared=ipc;\nsockets=x11;\n[Environment]\nGSETTINGS_BACKEND=memory\nGSK_RENDERER=cairo\n"
            )
            command(
                [
                    "gpg",
                    "--batch",
                    "--pinentry-mode",
                    "loopback",
                    "--passphrase",
                    "",
                    "--quick-generate-key",
                    "Local theme test <theme-test@example.invalid>",
                    "ed25519",
                    "sign",
                    "0",
                ],
                env,
            )
            keys = command(
                ["gpg", "--batch", "--with-colons", "--list-secret-keys"], env
            )
            fingerprint = next(
                line.split(":")[9]
                for line in keys.splitlines()
                if line.startswith("fpr:")
            )
            public_key = base / "test-public-key.asc"
            public_key.write_text(
                command(["gpg", "--batch", "--armor", "--export", fingerprint], env)
            )
            command(["flatpak", "build-finish", str(app)], env)
            repo = base / "repo"
            for tree, is_runtime in [(runtime, True), (app, False)]:
                command(
                    [
                        "flatpak",
                        "build-export",
                        *(["--runtime"] if is_runtime else []),
                        "--arch=" + arch,
                        "--gpg-sign=" + fingerprint,
                        "--gpg-homedir=" + env["GNUPGHOME"],
                        str(repo),
                        str(tree),
                        branch,
                    ],
                    env,
                )
            command(
                [
                    "flatpak",
                    "remote-add",
                    "--user",
                    "--gpg-import=" + str(public_key),
                    "amoled-local-test",
                    repo.as_uri(),
                ],
                env,
            )
            command(
                [
                    "flatpak",
                    "install",
                    "--user",
                    "--noninteractive",
                    "--assumeyes",
                    "amoled-local-test",
                    ref,
                ],
                env,
            )
            command(
                [
                    "flatpak",
                    "install",
                    "--user",
                    "--noninteractive",
                    "--assumeyes",
                    "amoled-local-test",
                    app_name,
                ],
                env,
            )
            cli = ["bash", str(ROOT / "install.sh")]
            gtk_version = command(["pkg-config", "--modversion", "gtk4"], env)
            app_mode = (
                "modern"
                if tuple(map(int, gtk_version.split(".")[:2])) >= (4, 16)
                else "legacy"
            )
            app_selection = app_name + "=" + app_mode

            def probe(light=False):
                output = command(
                    ["flatpak", "run", app_name, *(["--light"] if light else [])], env
                )
                return json.loads(output.splitlines()[-1])

            if not PREPARE_ONLY:
                before = probe()
                self.assertNotEqual(before["background"], [0, 0, 0])
            command(
                cli + ["--flatpak", app_selection],
                env,
            )
            app_css = home / ".var/app" / app_name / "config/gtk-4.0/gtk.css"
            self.assertTrue(app_css.is_file())
            if not PREPARE_ONLY:
                for light in [False, True]:
                    painted = probe(light)
                    self.assertEqual(painted["background"], [0, 0, 0], painted)
                    self.assertEqual(painted["accent"], [138, 180, 248], painted)
                    self.assertEqual(
                        "gtk-modern.css" in str(app_css.resolve()),
                        tuple(painted["gtk"]) >= (4, 16, 0),
                    )
                    print("Actual sandbox:", json.dumps(painted), "light=", light)
            command(
                [
                    "flatpak",
                    "override",
                    "--user",
                    "--filesystem=xdg-music:ro",
                    "--env=LATER_USER_SETTING=keep",
                    app_name,
                ],
                env,
            )
            command(cli + ["--flatpak", app_selection], env)
            command(cli + ["--remove", "--flatpak", app_selection], env)
            self.assertFalse(app_css.exists())
            override = Path(env["FLATPAK_USER_DIR"]) / "overrides" / app_name
            self.assertIn("xdg-music:ro", override.read_text())
            self.assertIn("LATER_USER_SETTING=keep", override.read_text())
            self.assertIn(
                "!" + str(home / "data/themes/Adwaita-AMOLED"), override.read_text()
            )
            self.assertTrue((home / "data/themes/Adwaita-AMOLED/index.theme").exists())
            if not PREPARE_ONLY:
                self.assertNotEqual(probe()["background"], [0, 0, 0])
            command(cli + ["--remove"], env)
            print(
                "Signed repository, real Flatpak install, explicit runtime selection, permissions, update and per-app removal passed. Sandbox executed:",
                not PREPARE_ONLY,
            )


if __name__ == "__main__":
    from report import main

    main()
