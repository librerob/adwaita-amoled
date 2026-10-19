#!/usr/bin/env python3
"""Exercise a real file manager in a fresh non-root D-Bus/Xvfb session.

Requires the selected app, csd-xsettings, xdotool, GTK3 introspection, and the
normal installer dependencies. PCManFM-Qt additionally uses qt5ct in this test.
Only disposable HOME/config/data directories are configured. Example:
dbus-run-session -- xvfb-run -a python3 tests/filemanager_icons.py nemo purple /tmp/evidence
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import test_installer as base


def require_isolated_session():
    if os.geteuid() == 0:
        raise RuntimeError("Run this GUI test as an ordinary user, not root.")
    ancestors = set()
    pid = os.getppid()
    for _ in range(20):
        if pid <= 1:
            break
        process = Path("/proc") / str(pid)
        args = (process / "cmdline").read_bytes().split(b"\0")
        ancestors.update(Path(os.fsdecode(arg)).name for arg in args[:3] if arg)
        status = (process / "status").read_text()
        pid = int(next(line.split()[1] for line in status.splitlines() if line.startswith("PPid:")))
    if not {"dbus-run-session", "xvfb-run"}.issubset(ancestors):
        raise RuntimeError("Use a fresh dbus-run-session and xvfb-run; do not run in a normal desktop session.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", choices=("nemo", "thunar", "caja", "nautilus", "pcmanfm-qt"))
    parser.add_argument("accent", choices=("blue", "yellow", "gold", "purple", "green", "red", "orange", "pink"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require_isolated_session()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = base.InstallerTests()
    fixture.setUp()
    env = dict(fixture.env, XDG_CURRENT_DESKTOP="X-Cinnamon", GSETTINGS_BACKEND="keyfile",
               GSK_RENDERER="cairo", LIBGL_ALWAYS_SOFTWARE="1", XDG_SESSION_TYPE="x11")
    env.pop("GTK_THEME", None)
    runtime = fixture.base / "runtime"
    runtime.mkdir(mode=0o700)
    env["XDG_RUNTIME_DIR"] = str(runtime)
    browse = fixture.base / "Browse"
    folders = ("Desktop", "Documents", "Downloads", "Music", "Pictures", "Videos", "Templates", "Public", "Projects")
    for name in folders:
        (browse / name).mkdir(parents=True)
    user_dirs = {"DESKTOP": "Desktop", "DOCUMENTS": "Documents", "DOWNLOAD": "Downloads",
                 "MUSIC": "Music", "PICTURES": "Pictures", "VIDEOS": "Videos",
                 "TEMPLATES": "Templates", "PUBLICSHARE": "Public"}
    fixture.write(fixture.config / "user-dirs.dirs", "".join(
        f'XDG_{key}_DIR="{browse / name}"\n' for key, name in user_dirs.items()))

    def run(command, check=True):
        if command[:2] == ["xdotool", "key"]:
            command = command[:2] + ["--clearmodifiers", "--delay", "80"] + command[2:]
        return subprocess.run(command, env=env, text=True, capture_output=True, check=check, timeout=30)

    log = (output / "application.log").open("w")
    processes = []
    try:
        fixture.run_cli("-l", "--gtk4-mode", "modern", "--activate", "--activate-icons", "--accent", args.accent,
                        "--extras", "qt", env=env)
        run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", base.THEME])
        run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", base.THEME])
        run(["dbus-update-activation-environment", "HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
             "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "GSETTINGS_BACKEND", "DISPLAY", "XAUTHORITY", "XDG_SESSION_TYPE"])
        service = subprocess.Popen(["csd-xsettings"], env=env, stdout=log, stderr=log)
        processes.append(service)
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gdk
        Gtk.init([])
        deadline = time.monotonic() + 10
        settings = Gtk.Settings.get_default()
        while any(settings.get_property(name) != base.THEME for name in ("gtk-icon-theme-name", "gtk-theme-name")):
            if time.monotonic() > deadline:
                raise AssertionError("Cinnamon xsettings did not select the GTK and icon themes")
            while Gtk.events_pending():
                Gtk.main_iteration()
            time.sleep(0.05)
        if args.app == "pcmanfm-qt":
            env["QT_QPA_PLATFORM"] = "xcb"
            env["QT_QPA_PLATFORMTHEME"] = "qt5ct"
            from PyQt5.QtCore import QSettings
            qt_settings = QSettings(str(fixture.config / "qt5ct/qt5ct.conf"), QSettings.IniFormat)
            qt_settings.setValue("Appearance/color_scheme_path", str(fixture.config / "qt5ct/colors/Adwaita-AMOLED.conf"))
            qt_settings.setValue("Appearance/custom_palette", True)
            qt_settings.setValue("Appearance/icon_theme", base.THEME)
            qt_settings.setValue("Appearance/style", "Fusion")
            qt_settings.sync()
        command = [args.app]
        if args.app == "caja":
            command.append("--no-desktop")
        command.append(str(browse))
        application = subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=True)
        processes.append(application)
        deadline = time.monotonic() + 20
        window = None
        pattern = {"nautilus": "[Nn]autilus", "thunar": "[Tt]hunar", "pcmanfm-qt": "[Pp][Cc][Mm]an[Ff][Mm]"}.get(args.app, args.app)
        while time.monotonic() < deadline:
            result = run(["xdotool", "search", "--onlyvisible", "--class", pattern], check=False)
            if result.stdout.splitlines():
                window = result.stdout.splitlines()[-1]
                break
            if application.poll() not in (None, 0):
                raise AssertionError(f"{args.app} exited early; see {output / 'application.log'}")
            time.sleep(0.1)
        assert window, f"No {args.app} window; see {output / 'application.log'}"
        run(["xdotool", "windowsize", window, "1120", "800"])
        run(["xdotool", "windowmove", window, "0", "0"])
        run(["xdotool", "windowfocus", "--sync", window])
        run(["xdotool", "key", "ctrl+2" if args.app == "nautilus" else "ctrl+1"])
        run(["xdotool", "key", "ctrl+plus"])
        time.sleep(1.5)
        run(["xdotool", "mousemove", "800", "650", "click", "1"])
        time.sleep(0.2)
        import sys
        sys.path.insert(0, str(base.ROOT / "tools"))
        import generate_palette as palette
        face = bytes.fromhex(palette.preset_colors(base.ROOT, args.accent)["accent_text"][1:])

        def capture(name, minimum=2000):
            image = Gdk.pixbuf_get_from_window(Gdk.get_default_root_window(), 0, 0, 1120, 800)
            image.savev(str(output / (name + ".png")), "png", [], [])
            pixels = bytes(image.get_pixels())
            count = pixels.count(face)
            assert count > minimum, f"{args.app}/{args.accent}: only {count} pixels match the folder face; see {name}.png"
            return pixels, count

        before, normal_count = capture("folders")
        run(["xdotool", "key", "ctrl+a"])
        time.sleep(0.15)
        selected, selected_count = capture("selected", minimum=500 if args.app == "caja" else 2000)
        # Caja deliberately colorizes selected icons; their unselected/sidebar
        # faces must still match. Selection itself must visibly change the view.
        assert sum(a != b for a, b in zip(before, selected)) > 4000, "Selection did not visibly change"
        run(["xdotool", "key", "Escape"])
        run(["xdotool", "mousemove", "800", "500", "click", "1"])
        time.sleep(0.15)
        before_menu, _ = capture("before-menu")
        run(["xdotool", "click", "3"])
        time.sleep(0.3)
        menu, menu_count = capture("context-menu")
        assert sum(a != b for a, b in zip(before_menu, menu)) > 4000, "Context menu did not visibly open"
        run(["xdotool", "key", "Escape"])
        time.sleep(0.2)
        run(["xdotool", "windowfocus", "--sync", window])
        run(["xdotool", "key", "ctrl+l"])
        time.sleep(0.2)
        run(["xdotool", "key", "ctrl+a"])
        run(["xdotool", "type", "--clearmodifiers", "--delay", "20", str(browse / "Documents")])
        run(["xdotool", "key", "Return"])
        deadline = time.monotonic() + 10
        while "Documents" not in run(["xdotool", "getwindowname", window]).stdout:
            if time.monotonic() > deadline:
                image = Gdk.pixbuf_get_from_window(Gdk.get_default_root_window(), 0, 0, 1120, 800)
                image.savev(str(output / "navigation-failure.png"), "png", [], [])
                raise AssertionError("Could not navigate to Documents")
            time.sleep(0.1)
        time.sleep(0.4)
        run(["xdotool", "windowfocus", "--sync", window])
        run(["xdotool", "key", "alt+Left"])
        deadline = time.monotonic() + 10
        while "Browse" not in run(["xdotool", "getwindowname", window]).stdout:
            if time.monotonic() > deadline:
                raise AssertionError("Could not navigate back to Browse")
            time.sleep(0.1)
        time.sleep(0.6)
        run(["xdotool", "mousemove", "800", "650", "click", "1"])
        time.sleep(0.2)
        _, returned_count = capture("returned")
        assert "Theme pars" not in (output / "application.log").read_text(), "GTK CSS parser errors; see application.log"
        report = {"app": args.app, "accent": args.accent, "status": "passed",
                  "normal_pixels": normal_count, "selected_pixels": selected_count,
                  "menu_pixels": menu_count, "returned_pixels": returned_count,
                  "uid": os.geteuid(), "gtk_theme_environment": env.get("GTK_THEME"), "display": "isolated Xvfb/X11"}
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    finally:
        subprocess.run([args.app, "--quit"], env=env, capture_output=True, timeout=10)
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        log.close()
        fixture.doCleanups()


if __name__ == "__main__":
    main()
