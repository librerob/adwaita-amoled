"""Drive real Bash menus through a pseudo-terminal, using disposable user paths."""

import errno
import fcntl
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import termios
import sys
import tarfile
import time
import unittest

import test_installer as base


class Terminal:
    def __init__(self, source, env, args=()):
        self.master, slave = pty.openpty()
        self.output = ""
        self.cursor = 0

        def session():
            os.setsid()
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        self.process = subprocess.Popen(
            ["/bin/bash", str(source / "install.sh"), *args],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            preexec_fn=session,
        )
        os.close(slave)

    def read(self, timeout):
        if not select.select([self.master], [], [], timeout)[0]:
            return True
        try:
            data = os.read(self.master, 65536)
        except OSError as error:
            if error.errno != errno.EIO:
                raise
            return False
        if not data:
            return False
        self.output += data.decode("utf-8", errors="replace").replace("\r\n", "\n")
        return True

    def expect(self, text, timeout=15):
        deadline = time.monotonic() + timeout
        while text not in self.output[self.cursor :]:
            if time.monotonic() >= deadline or not self.read(0.1):
                raise AssertionError(f"Expected {text!r} in terminal:\n{self.output}")
        self.cursor = self.output.index(text, self.cursor) + len(text)

    def send(self, value):
        os.write(self.master, (value + "\n").encode())

    def answer(self, prompt, value):
        self.expect(prompt)
        self.send(value)

    def finish(self, expected=0):
        deadline = time.monotonic() + 15
        while self.read(0.1):
            if time.monotonic() >= deadline:
                raise AssertionError(f"Terminal did not finish:\n{self.output}")
        result = self.process.wait(timeout=5)
        if result != expected:
            raise AssertionError(f"Exit {result}, expected {expected}:\n{self.output}")
        return self.output

    def close(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGKILL)
        self.process.wait(timeout=5)
        os.close(self.master)


class GuidedInstallerTests(unittest.TestCase):
    def setUp(self):
        base.InstallerTests.setUp(self)
        self.env["XDG_CURRENT_DESKTOP"] = ""
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name in [
            "bash",
            "dirname",
            "realpath",
            "rm",
            "mkdir",
            "cp",
            "ln",
            "chmod",
            "mv",
            "mktemp",
            "flock",
            "stat",
            "sha256sum",
            "cat",
        ]:
            (self.bin / name).symlink_to(shutil.which(name))
        # No Python, dialog, whiptail, fzf or optional desktop programs in PATH.
        self.env["PATH"] = str(self.bin)

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)

    def terminal(self, args=(), source=base.ROOT):
        terminal = Terminal(source, self.env, args)
        self.addCleanup(terminal.close)
        return terminal

    def install_choices(self, terminal, gtk="n", extras="n"):
        terminal.answer("Choose [1]:", "1")
        terminal.answer("Apply the theme to native GTK4/libadwaita apps too?", gtk)
        terminal.answer("Copy optional application themes or wallpaper?", extras)

    def test_release_archive_contains_and_runs_guided_setup(self):
        archive = self.base / "runtime.tar.gz"
        subprocess.run(
            [sys.executable, str(base.ROOT / "tools/package.py"), str(archive)],
            capture_output=True,
            check=True,
        )
        with tarfile.open(archive) as package:
            package.extractall(self.base / "extracted", filter="data")
        source = self.base / "extracted" / base.THEME
        t = self.terminal(source=source)
        self.install_choices(t)
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertEqual(
            (self.theme / "setup-menu.sh").read_bytes(),
            (source / "setup-menu.sh").read_bytes(),
        )
        self.assertTrue((self.theme / "gtk-4.0/gtk.gresource").is_file())

    def test_bare_terminal_guides_and_installs_gtk4_without_python(self):
        self.fake("pkg-config", "echo 4.24.1")
        t = self.terminal()
        self.install_choices(t, gtk="")
        t.answer("Apply these changes?", "y")
        text = t.finish()
        self.assertIn("GTK4 overrides (modern):", text)
        self.assertEqual(
            (self.config / "gtk-4.0/gtk.css").resolve(),
            self.theme / "extra/libadwaita/gtk-modern.css",
        )
        self.assertEqual(
            (self.theme / "gtk-3.0/gtk.gresource").read_bytes(),
            (base.ROOT / "gtk-3.0/gtk.gresource").read_bytes(),
        )
        self.assertFalse((self.home / "state").exists())

    def test_cancel_and_preview_make_no_files_or_settings(self):
        for reply in ["", "n", "p"]:
            with self.subTest(reply=reply):
                t = self.terminal()
                self.install_choices(t)
                t.answer("Apply these changes?", reply)
                text = t.finish()
                self.assertIn(
                    "Dry run: nothing changed." if reply == "p" else "Cancelled", text
                )
                self.assertEqual(list(self.home.iterdir()), [])

    def test_help_invalid_input_and_exit_do_not_install(self):
        t = self.terminal()
        t.answer("Choose [1]:", "bogus")
        t.expect("Enter a number from 0 to 5.")
        t.answer("Choose [1]:", "3")
        t.expect("For command-line options")
        t.answer("Choose [1]:", "0")
        t.finish()
        self.assertEqual(list(self.home.iterdir()), [])

    def test_eof_and_ctrl_c_before_confirmation_do_not_change_files(self):
        t = self.terminal()
        t.expect("Choose [1]:")
        os.write(t.master, b"\x04")
        self.assertIn("Cancelled", t.finish())
        t = self.terminal()
        self.install_choices(t)
        t.expect("Apply these changes?")
        os.write(t.master, b"\x03")
        t.finish(expected=-signal.SIGINT)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_existing_gtk4_overrides_default_to_keep_and_review_names_replacements(
        self,
    ):
        directory = self.config / "gtk-4.0"
        directory.mkdir(parents=True)
        original = directory / "gtk.css"
        original.write_text("/* personal override */")
        self.fake("pkg-config", "echo 4.14.5")
        t = self.terminal()
        self.install_choices(t, gtk="y")
        t.expect("Existing: " + str(original))
        t.answer("Apply these changes?", "n")
        t.finish()
        self.assertEqual(original.read_text(), "/* personal override */")
        t = self.terminal()
        self.install_choices(t, gtk="")
        t.answer("Apply these changes?", "y")
        text = t.finish()
        self.assertNotIn("GTK4 overrides (", text)
        self.assertFalse(original.is_symlink())
        self.assertEqual(original.read_text(), "/* personal override */")

    def test_unknown_gtk_version_can_be_skipped_without_guessing(self):
        t = self.terminal(("--interactive",))
        self.install_choices(t, gtk="y")
        t.expect("Could not detect native GTK4.")
        t.answer("Choose [0]:", "0")
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertTrue(self.theme.is_dir())
        self.assertFalse(self.config.exists())

    def test_explicit_options_never_prompt_even_in_a_terminal(self):
        t = self.terminal(("install",))
        text = t.finish()
        self.assertNotIn("Adwaita-AMOLED setup", text)
        self.assertTrue(self.theme.is_dir())
        self.assertFalse(self.config.exists())

    def test_interactive_requires_terminal_and_rejects_mixed_flags(self):
        for args in [("--interactive",), ("--interactive", "--remove")]:
            result = base.InstallerTests.run_cli(self, *args, success=False)
            self.assertIn("terminal" if len(args) == 1 else "by itself", result.stderr)
            self.assertFalse(self.theme.exists())

    def test_selected_extras_create_folders_and_keep_personal_config(self):
        personal = self.config / "kitty/kitty.conf"
        personal.parent.mkdir(parents=True)
        personal.write_text("font_size 14\n")
        t = self.terminal()
        self.install_choices(t, extras="y")
        for choice in ["2", "0"]:
            t.answer("Choose [0]:", choice)
        t.answer("Apply these changes?", "p")
        preview = t.finish()
        self.assertIn("Dry run: nothing changed.", preview)
        self.assertNotIn("App theme files copied.", preview)
        self.assertFalse(self.theme.exists())
        self.assertFalse((self.config / "kitty/themes").exists())
        t = self.terminal()
        self.install_choices(t, extras="y")
        for choice in ["2", "2", "2", "5", "0"]:
            t.answer("Choose [0]:", choice)
        t.expect(
            "Kitty snippet: " + str(self.config / "kitty/themes/adwaita-amoled.conf")
        )
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertEqual(personal.read_text(), "font_size 14\n")
        self.assertTrue((self.config / "nvim/colors/adwaita-amoled.vim").is_file())
        self.assertTrue((self.config / "kitty/themes/adwaita-amoled.conf").is_file())
        self.assertFalse((self.config / "qt5ct").exists())
        t = self.terminal()
        t.answer("Choose [1]:", "2")
        t.expect("Native GTK4 links pointing to this theme are removed automatically")
        t.answer("Also remove selected copied app themes or wallpaper?", "y")
        for choice in ["2", "5", "0"]:
            t.answer("Choose [0]:", choice)
        t.answer("Apply these changes?", "y")
        self.assertIn("Selected app theme files removed.", t.finish())
        self.assertFalse((self.config / "kitty/themes/adwaita-amoled.conf").exists())
        self.assertFalse((self.config / "nvim/colors/adwaita-amoled.vim").exists())
        self.assertEqual(personal.read_text(), "font_size 14\n")

    def test_supported_shell_matches_and_unsupported_shell_is_not_offered(self):
        self.env["XDG_CURRENT_DESKTOP"] = "GNOME"
        self.fake("gsettings", "echo false")
        self.fake("gnome-extensions", "exit 0")
        for version in ["46.10", "48.0"]:
            self.fake("gnome-shell", "echo 'GNOME Shell " + version + "'")
            t = self.terminal()
            t.answer("Choose [1]:", "1")
            t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
            t.answer("Select Adwaita-AMOLED for this desktop now?", "y")
            if version == "46.10":
                t.answer(
                    "Apply the matching GNOME Shell theme with User Themes too?", "y"
                )
            else:
                t.expect("Shell styling is verified only for GNOME 46/51")
            t.answer("Copy optional application themes or wallpaper?", "n")
            t.answer("Apply these changes?", "y")
            text = t.finish()
            if version == "46.10":
                self.assertEqual(
                    (self.theme / "gnome-shell/gnome-shell.css").read_bytes(),
                    (base.ROOT / "gnome-shell/gnome-shell-46.css").read_bytes(),
                )
            else:
                self.assertNotIn(
                    "Apply the matching GNOME Shell theme with User Themes too?", text
                )

    def test_missing_user_themes_does_not_block_gnome_gtk_installation(self):
        self.env["XDG_CURRENT_DESKTOP"] = "GNOME"
        self.fake("gsettings", "echo false")
        self.fake("gnome-shell", "echo 'GNOME Shell 46.10'")
        t = self.terminal()
        t.answer("Choose [1]:", "1")
        t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
        t.answer("Select Adwaita-AMOLED for this desktop now?", "y")
        t.expect("To apply them, install/allow User Themes")
        t.answer("Copy optional application themes or wallpaper?", "n")
        t.answer("Apply these changes?", "y")
        self.assertNotIn(
            "Apply the matching GNOME Shell theme with User Themes too?", t.finish()
        )
        self.assertTrue(self.theme.is_dir())

    def test_budgie_gnome_session_does_not_offer_gnome_shell_activation(self):
        self.env["XDG_CURRENT_DESKTOP"] = "Budgie:GNOME"
        self.fake("gsettings", "echo false")
        self.fake("gnome-extensions", "exit 0")
        self.fake("gnome-shell", "echo 'GNOME Shell 46.10'")
        t = self.terminal()
        t.answer("Choose [1]:", "1")
        t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
        t.answer("Select Adwaita-AMOLED for this desktop now?", "y")
        t.answer("Copy optional application themes or wallpaper?", "n")
        t.answer("Apply these changes?", "y")
        self.assertNotIn(
            "Apply the matching GNOME Shell theme with User Themes too?", t.finish()
        )

    def test_desktop_selection_happens_only_after_confirmation(self):
        self.env["XDG_CURRENT_DESKTOP"] = "Cinnamon"
        log = self.base / "settings.log"
        self.env["SETTINGS_LOG"] = str(log)
        self.fake(
            "gsettings",
            'case $1 in get) echo "old-theme" ;; range) exit 1 ;; *) printf "%s\\n" "$*" >> "$SETTINGS_LOG" ;; esac',
        )
        for apply in ["n", "y"]:
            t = self.terminal()
            t.answer("Choose [1]:", "1")
            t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
            t.answer("Select Adwaita-AMOLED for this desktop now?", "y")
            t.answer("Copy optional application themes or wallpaper?", "n")
            t.expect("Apply these changes?")
            self.assertFalse(log.exists())
            t.send(apply)
            t.finish()
        self.assertEqual(len(log.read_text().splitlines()), 3)

    def test_dark_preference_review_cancel_preview_and_apply(self):
        log = self.base / "appearance.log"
        self.env["SETTINGS_LOG"] = str(log)
        self.fake(
            "gsettings",
            """case $1 in
range) printf "enum\\n'prefer-dark'\\n'default'\\n'prefer-light'\\n" ;;
get) echo "'Original'" ;;
writable) echo true ;;
set) printf '%s\\n' "$*" >> "$SETTINGS_LOG" ;;
*) exit 1 ;;
esac""",
        )
        for desktop, answer in [
            ("Cinnamon", "n"),
            ("Cinnamon", "p"),
            ("GNOME", "y"),
            ("Cinnamon", "y"),
        ]:
            with self.subTest(desktop=desktop, answer=answer):
                if log.exists():
                    log.unlink()
                self.env["XDG_CURRENT_DESKTOP"] = desktop
                t = self.terminal()
                t.answer("Choose [1]:", "1")
                t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
                t.answer("Select Adwaita-AMOLED for this desktop now?", "n")
                t.answer("Copy optional application themes or wallpaper?", "n")
                t.expect("org.gnome.desktop.interface color-scheme = prefer-dark")
                t.expect("Apply these changes?")
                self.assertFalse(log.exists())
                t.send(answer)
                output = t.finish()
                self.assertNotIn(
                    "Prefer dark appearance in applications such as Firefox?", output
                )
                if answer == "y":
                    expected = [
                        "set org.gnome.desktop.interface color-scheme prefer-dark"
                    ]
                    if desktop == "Cinnamon":
                        expected.insert(
                            0, "set org.x.apps.portal color-scheme prefer-dark"
                        )
                    self.assertEqual(log.read_text().splitlines(), expected)
                else:
                    self.assertFalse(log.exists())
                    self.assertFalse(self.theme.exists())
                    if answer == "p":
                        self.assertIn(
                            "gsettings set org.x.apps.portal color-scheme prefer-dark",
                            output,
                        )

    def test_color_menu_installs_and_retains_selected_accent_without_python(self):
        t = self.terminal()
        t.answer("Choose [1]:", "5")
        t.answer("Choose [0]:", "3")  # gold
        t.answer("Choose [1]:", "1")
        t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
        t.answer("Copy optional application themes or wallpaper?", "n")
        t.expect("Accent color: gold")
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertEqual((self.theme / "accent-name").read_text(), "gold\n")
        self.assertEqual(
            (self.theme / "gtk-3.0/gtk.gresource").read_bytes(),
            (base.ROOT / "accents/gold/gtk-3.0/gtk.gresource").read_bytes(),
        )
        self.assertFalse((self.theme / "accents").exists())
        t = self.terminal()
        t.expect("Accent color (gold)")
        self.install_choices(t)
        t.expect("Accent color: gold")
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertEqual((self.theme / "accent-name").read_text(), "gold\n")

    def test_unavailable_dark_preference_does_not_add_question_or_block_installation(
        self,
    ):
        self.env["XDG_CURRENT_DESKTOP"] = "GNOME"
        self.fake(
            "gsettings",
            """case $1 in
range) printf "enum\\n'prefer-dark'\\n" ;;
get) echo "'Original'" ;;
writable) echo false ;;
*) exit 99 ;;
esac""",
        )
        t = self.terminal()
        t.answer("Choose [1]:", "1")
        t.answer("Apply the theme to native GTK4/libadwaita apps too?", "n")
        t.answer("Select Adwaita-AMOLED for this desktop now?", "n")
        t.answer("Copy optional application themes or wallpaper?", "n")
        t.answer("Apply these changes?", "y")
        output = t.finish()
        self.assertNotIn("Application appearance: prefer-dark", output)
        self.assertNotIn(
            "Prefer dark appearance in applications such as Firefox?", output
        )
        self.assertIn("App appearance unchanged", output)
        self.assertTrue(self.theme.is_dir())

    def flatpak(self):
        log = self.base / "flatpak.log"
        self.env["FLATPAK_LOG"] = str(log)
        self.fake(
            "flatpak",
            """case $1 in
list) printf 'org.example.One\tFirst app\norg.example.Two\tSecond app\n' ;;
info) exit 0 ;;
override) printf '%s\n' "$*" >> "$FLATPAK_LOG" ;;
esac""",
        )
        return log

    def select_flatpak(self, t, action):
        t.answer("Choose [1]:", "4")
        t.answer("Choose [0]:", action)
        t.answer("Choose [0]:", "1")
        t.answer("Choose [0]:", "3")
        t.answer("Choose [0]:", "0")

    def test_selected_flatpak_configuration_and_removal_keep_other_apps(self):
        log = self.flatpak()
        other = self.home / ".var/app/org.example.Two/config/gtk-4.0/gtk.css"
        other.parent.mkdir(parents=True)
        other.write_text("peer custom css")
        for action in ["2", "3"]:
            t = self.terminal()
            self.select_flatpak(t, action)
            t.answer("Apply these changes?", "y")
            text = t.finish()
            css = self.home / ".var/app/org.example.One/config/gtk-4.0/gtk.css"
            self.assertEqual(css.is_symlink(), action == "2")
            self.assertTrue(self.theme.is_dir())
            self.assertEqual(other.read_text(), "peer custom css")
            if action == "3":
                self.assertIn("installed theme files will be kept", text)
        self.assertEqual(len(log.read_text().splitlines()), 2)
        self.assertNotIn("org.example.Two", log.read_text())

    def test_empty_flatpak_removal_selection_does_not_fall_through_to_theme_removal(
        self,
    ):
        self.flatpak()
        self.theme.mkdir(parents=True)
        marker = self.theme / "keep"
        marker.write_text("existing theme")
        t = self.terminal()
        for prompt, answer in [
            ("Choose [1]:", "4"),
            ("Choose [0]:", "3"),
            ("Choose [0]:", "0"),
            ("Choose [0]:", "0"),
            ("Choose [1]:", "0"),
        ]:
            t.answer(prompt, answer)
        t.finish()
        self.assertEqual(marker.read_text(), "existing theme")

    def test_duplicate_flatpak_ids_are_shown_once(self):
        self.fake(
            "flatpak",
            "printf 'org.example.One\\tFirst app\\norg.example.One\\tFirst app\\norg.example.Two\\tSecond app\\n'",
        )
        t = self.terminal()
        for prompt, answer in [
            ("Choose [1]:", "4"),
            ("Choose [0]:", "2"),
            ("Choose [0]:", "0"),
            ("Choose [0]:", "0"),
            ("Choose [1]:", "0"),
        ]:
            t.answer(prompt, answer)
        text = (
            t.finish()
            .split("Select an installed Flatpak application:", 1)[1]
            .split("0. Done", 1)[0]
        )
        self.assertEqual(text.count("(org.example.One)"), 1)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_removal_is_reviewed_and_uses_existing_link_cleanup(self):
        base.InstallerTests.run_cli(self, "-l", "--gtk4-mode", "legacy")
        t = self.terminal()
        t.answer("Choose [1]:", "2")
        t.expect("Native GTK4 links pointing to this theme are removed automatically")
        t.answer("Also remove selected copied app themes or wallpaper?", "n")
        t.expect("Remove theme files:")
        t.answer("Apply these changes?", "y")
        t.finish()
        self.assertFalse(self.theme.exists())
        self.assertFalse(os.path.lexists(self.config / "gtk-4.0/gtk.css"))

    def test_administrator_handoff_passes_only_the_guided_entry_point(self):
        log = self.base / "sudo.log"
        self.env["SUDO_LOG"] = str(log)
        self.fake("sudo", 'printf "%s\\n" "$@" > "$SUDO_LOG"')
        t = self.terminal()
        t.answer("Choose [1]:", "4")
        t.answer("Choose [0]:", "1")
        t.finish()
        self.assertEqual(
            log.read_text().splitlines(),
            ["--", "bash", str(base.ROOT / "install.sh"), "--interactive"],
        )
        self.assertEqual(list(self.home.iterdir()), [])


class SystemMenuTests(unittest.TestCase):
    setUp = GuidedInstallerTests.setUp
    terminal = GuidedInstallerTests.terminal

    def test_shared_color_choice_is_in_the_review_without_writing_system_paths(self):
        self.assertEqual(os.geteuid(), 0)
        self.env["SUDO_USER"] = "desktop-user"
        t = self.terminal(("--interactive",))
        t.answer("Choose [0]:", "3")
        t.answer("Choose [0]:", "8")
        t.answer("Choose [0]:", "1")
        t.answer("Choose [1]:", "2")
        t.answer("Apply these changes?", "p")
        text = t.finish()
        self.assertIn("Accent color: pink", text)
        self.assertIn("/usr/share/themes/Adwaita-AMOLED", text)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_shared_setup_preview_and_cancel_never_write_system_paths(self):
        self.assertEqual(os.geteuid(), 0)
        self.env["SUDO_USER"] = "desktop-user"
        paths = [
            Path("/usr/local/share/themes/Adwaita-AMOLED"),
            Path("/usr/share/themes/Adwaita-AMOLED"),
        ]
        before = [p.lstat() if os.path.lexists(p) else None for p in paths]
        for answer in ["p", "n"]:
            t = self.terminal(("--interactive",))
            t.answer("Choose [0]:", "1")
            t.answer("Choose [1]:", "1")
            t.answer("Also manage a link under /usr/share/themes", "y")
            t.answer("Apply these changes?", answer)
            text = t.finish()
            self.assertIn("/usr/local/share/themes/Adwaita-AMOLED", text)
            self.assertIn("Shared link: /usr/share/themes/Adwaita-AMOLED", text)
        self.assertEqual(
            [p.lstat() if os.path.lexists(p) else None for p in paths], before
        )
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    from report import main

    main()
