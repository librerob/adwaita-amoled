"""Direct Bash installation in isolated HOME/XDG directories."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
THEME = "Adwaita-AMOLED"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="amoled-bash-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.home = self.base / "home with space # % ü"
        self.home.mkdir()
        self.config = self.home / "config"
        self.data = self.home / "data"
        self.theme = self.data / "themes" / THEME
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.config),
            XDG_DATA_HOME=str(self.data),
            XDG_STATE_HOME=str(self.home / "state"),
            XDG_CACHE_HOME=str(self.home / "cache"),
            XDG_CONFIG_DIRS=str(self.home / "empty-system-config"),
            GSETTINGS_BACKEND="memory",
        )
        for key in [
            "SUDO_USER",
            "SUDO_UID",
            "GTK_THEME",
            "NVIM_APPNAME",
            "KITTY_CONFIG_DIRECTORY",
            "BAT_CONFIG_PATH",
            "BAT_CACHE_PATH",
            "BAT_THEME",
        ]:
            self.env.pop(key, None)

    def run_cli(self, *args, success=True, env=None, root=ROOT):
        result = subprocess.run(
            ["bash", str(root / "install.sh"), *args],
            env=env or self.env,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def fake_program(self, name, body):
        bin_dir = self.base / "bin"
        bin_dir.mkdir(exist_ok=True)
        p = bin_dir / name
        p.write_text("#!/bin/bash\n" + body + "\n")
        p.chmod(0o755)
        self.env["PATH"] = str(bin_dir) + ":" + os.environ["PATH"]
        return p

    def test_default_installs_compiled_theme_without_config_or_state(self):
        self.run_cli()
        for version in ["3.0", "4.0"]:
            self.assertEqual(
                (self.theme / f"gtk-{version}/gtk.gresource").read_bytes(),
                (ROOT / f"gtk-{version}/gtk.gresource").read_bytes(),
            )
        self.assertFalse(self.config.exists())
        self.assertFalse((self.home / "state").exists())
        self.assertFalse((self.theme / "src").exists())
        self.assertFalse((self.theme / "tools").exists())

    def test_changed_document_modes_and_old_state_do_not_block_updates(self):
        self.run_cli()
        p = self.theme / "COLOR_COMPLETENESS.md"
        p.write_text("older or locally copied document\n")
        p.chmod(0o755)
        state = self.home / "state/adwaita-amoled/state.json"
        self.write(state, '{"old-installer-state": "must stay untouched"}\n')
        before = state.read_bytes()
        self.run_cli("update", "--yes")
        self.assertEqual(p.read_bytes(), (ROOT / p.name).read_bytes())
        self.assertEqual(p.stat().st_mode & 0o777, 0o644)
        self.assertEqual(state.read_bytes(), before)
        self.assertEqual(list(state.parent.iterdir()), [state])

    def test_gtk4_links_replace_old_overrides_and_repeat_cleanly(self):
        directory = self.config / "gtk-4.0"
        self.write(directory / "gtk.css", "old complete override\n")
        self.write(directory / "assets/old.svg", "old asset")
        self.write(directory / "settings.ini", "[Settings]\ngtk-font-name=Sans 12\n")
        for mode, entry in [
            ("legacy", "gtk.css"),
            ("modern", "gtk-modern.css"),
            ("modern", "gtk-modern.css"),
        ]:
            self.run_cli("-l", "--gtk4-mode", mode)
            self.assertTrue((directory / "gtk.css").is_symlink())
            self.assertEqual(
                (directory / "gtk.css").resolve(),
                self.theme / "extra/libadwaita" / entry,
            )
            self.assertEqual(
                (directory / "gtk-dark.css").read_bytes(),
                (ROOT / "extra/libadwaita/gtk-dark.css").read_bytes(),
            )
            self.assertTrue((directory / "assets").is_symlink())
            self.assertFalse((directory / "assets/assets").exists())
            self.assertFalse((directory / "assets/old.svg").exists())
            self.assertEqual(
                (directory / "settings.ini").read_text(),
                "[Settings]\ngtk-font-name=Sans 12\n",
            )
        self.assertFalse(list(self.config.glob("*.backup*")))

    def test_dry_run_changes_nothing_even_with_gtk4_and_extras(self):
        self.run_cli("-l", "--gtk4-mode", "legacy", "--extras", "all", "--dry-run")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_remove_unlinks_theme_links_without_restoring_old_files(self):
        self.run_cli("-l", "--gtk4-mode", "legacy")
        self.run_cli("--remove", "-l")
        self.assertFalse(self.theme.exists())
        self.assertFalse(os.path.lexists(self.config / "gtk-4.0/gtk.css"))
        self.assertFalse(os.path.lexists(self.config / "gtk-4.0/assets"))
        self.assertFalse((self.home / "state").exists())

    def test_remove_preserves_replacement_custom_css(self):
        self.run_cli("-l", "--gtk4-mode", "legacy")
        css = self.config / "gtk-4.0/gtk.css"
        css.unlink()
        css.write_text("/* replacement user CSS */\n")
        self.run_cli("--remove", "-l")
        self.assertEqual(css.read_text(), "/* replacement user CSS */\n")

    def test_legacy_copy_is_refreshed_instead_of_shadowing_new_theme(self):
        legacy = self.home / ".themes" / THEME
        self.write(legacy / "gtk-3.0/gtk.css", "old theme")
        self.run_cli()
        self.assertEqual(
            (legacy / "gtk-3.0/gtk.gresource").read_bytes(),
            (self.theme / "gtk-3.0/gtk.gresource").read_bytes(),
        )
        self.run_cli("--remove")
        self.assertFalse(legacy.exists())

    def test_custom_destination_leaves_other_theme_copy_alone(self):
        legacy = self.home / ".themes" / THEME
        self.write(legacy / "keep", "untouched")
        dest = self.base / "custom parent"
        self.run_cli("--dest", str(dest))
        self.assertTrue((dest / THEME / "index.theme").exists())
        self.assertEqual((legacy / "keep").read_text(), "untouched")

    def test_no_python_interpreter_required(self):
        bin_dir = self.base / "minimal-bin"
        bin_dir.mkdir()
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
        ]:
            (bin_dir / name).symlink_to(shutil.which(name))
        env = dict(self.env, PATH=str(bin_dir))
        result = subprocess.run(
            ["/bin/bash", str(ROOT / "install.sh"), "-l", "--gtk4-mode", "legacy"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.config / "gtk-4.0/gtk.css").is_symlink())

    def test_gtk_version_detection_selects_old_and_modern_entry_points(self):
        for version, entry in [
            ("4.14.5", "gtk.css"),
            ("4.16.0", "gtk-modern.css"),
            ("4.24.1", "gtk-modern.css"),
        ]:
            self.fake_program("pkg-config", 'printf "%s\\n" ' + version)
            self.run_cli("-l")
            self.assertEqual((self.config / "gtk-4.0/gtk.css").resolve().name, entry)

    def test_shell_variants_follow_local_version_and_unsupported_shell_is_refused(self):
        for version in ["46.0", "51.1"]:
            self.fake_program("gnome-shell", 'echo "GNOME Shell ' + version + '"')
            self.run_cli("--shell")
            self.assertEqual(
                (self.theme / "gnome-shell/gnome-shell.css").read_bytes(),
                (ROOT / f"gnome-shell/gnome-shell-{version[:2]}.css").read_bytes(),
            )
        self.fake_program("gnome-shell", 'echo "GNOME Shell 48.0"')
        before = (self.theme / "gnome-shell/gnome-shell.css").read_bytes()
        self.run_cli("--shell", success=False)
        self.assertEqual(
            (self.theme / "gnome-shell/gnome-shell.css").read_bytes(), before
        )
        self.run_cli()  # Unverified Shell must not prevent a GTK-only install.

    def test_extras_create_theme_folders_and_leave_app_configs_untouched(self):
        originals = {
            "kitty/kitty.conf": "font_size 14\n",
            "nvim/init.lua": "vim.o.number = true\n",
            "alacritty/alacritty.toml": "[font]\nsize=14\n",
            "rofi/config.rasi": "configuration {}\n",
        }
        for name, text in originals.items():
            self.write(self.config / name, text)
        self.write(self.home / ".zshrc", "# existing shell config\n")
        self.run_cli("--extras", "all")
        for name, text in originals.items():
            self.assertEqual((self.config / name).read_text(), text)
        self.assertEqual(
            (self.home / ".zshrc").read_text(), "# existing shell config\n"
        )
        for name in [
            "kitty/themes/adwaita-amoled.conf",
            "alacritty/themes/adwaita-amoled.toml",
            "nvim/colors/adwaita-amoled.vim",
            "rofi/themes/adwaita-amoled.rasi",
            "zsh/adwaita-amoled.zsh",
            "qt5ct/colors/Adwaita-AMOLED.conf",
            "qt6ct/colors/Adwaita-AMOLED.conf",
        ]:
            self.assertTrue((self.config / name).is_file(), name)
        self.assertTrue(
            (self.data / "backgrounds/Adwaita-AMOLED/blackmount.png").is_file()
        )

    def test_custom_profiles(self):
        env = dict(
            self.env,
            NVIM_APPNAME="my-nvim",
            KITTY_CONFIG_DIRECTORY=str(self.home / "custom kitty"),
        )
        self.run_cli("--extras", "nvim,kitty", env=env)
        self.assertTrue((self.config / "my-nvim/colors/adwaita-amoled.vim").exists())
        self.assertTrue(
            (self.home / "custom kitty/themes/adwaita-amoled.conf").exists()
        )

    def test_invalid_options_stop_before_copying(self):
        for args in [
            ("--extras", "oops"),
            ("--gtk4-mode", "oops"),
            ("--dest",),
            ("--dest", "/"),
            ("--flatpak", "org.example.App"),
            ("--shell-version", "48"),
        ]:
            self.run_cli(*args, success=False)
            self.assertFalse(self.theme.exists())

    def test_sudo_requires_explicit_system_scope(self):
        self.run_cli(env=dict(self.env, SUDO_USER="desktop-user"), success=False)
        self.assertFalse(self.theme.exists())

    def test_source_inside_destination_is_rejected(self):
        source = self.base / "source" / THEME
        source.mkdir(parents=True)
        shutil.copy2(ROOT / "install.sh", source / "install.sh")
        self.run_cli("--dest", str(source.parent), root=source, success=False)
        self.assertTrue((source / "install.sh").is_file())

    def test_runtime_archive_is_reproducible_and_installs_without_source_or_python_tools(
        self,
    ):
        archives = [self.base / "one.tar.gz", self.base / "two.tar.gz"]
        for path in archives:
            subprocess.run(
                [sys.executable, str(ROOT / "tools/package.py"), str(path)],
                check=True,
                capture_output=True,
            )
        self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())
        unpacked = self.base / "unpacked"
        with tarfile.open(archives[0]) as archive:
            self.assertFalse(
                any(
                    "/tools/" in m.name or "/src/" in m.name
                    for m in archive.getmembers()
                )
            )
            archive.extractall(unpacked, filter="data")
        source = unpacked / THEME
        for line in (source / "ARCHIVE_CONTENTS.sha256").read_text().splitlines():
            checksum, name = line.split("  ", 1)
            self.assertEqual(
                hashlib.sha256((source / name).read_bytes()).hexdigest(), checksum
            )
        self.run_cli("-l", "--gtk4-mode", "legacy", root=source)
        self.run_cli("-l", "--gtk4-mode", "legacy", root=source)
        self.run_cli("--remove", "-l", root=source)
        self.assertFalse(self.theme.exists())


if __name__ == "__main__":
    from report import main

    main()
