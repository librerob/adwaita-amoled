"""Bash-installed theme files through real native consumers; use Xvfb."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstalledConsumerTests(unittest.TestCase):
    def run_program(self, arguments, env):
        result = subprocess.run(
            arguments, env=env, capture_output=True, text=True, timeout=120
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_native_gtk4_automatic_loading_and_removal(self):
        with tempfile.TemporaryDirectory(prefix="amoled-native-install-") as temporary:
            home = Path(temporary) / "home # % ü"
            home.mkdir()
            env = dict(
                os.environ,
                HOME=str(home),
                XDG_CONFIG_HOME=str(home / "config"),
                XDG_DATA_HOME=str(home / "data"),
                XDG_STATE_HOME=str(home / "state"),
                XDG_CACHE_HOME=str(home / "cache"),
                GSETTINGS_BACKEND="memory",
                GSK_RENDERER="cairo",
            )
            for name in ["SUDO_USER", "GTK_THEME", "GTK_PATH", "GTK_DATA_PREFIX"]:
                env.pop(name, None)
            self.run_program(
                [
                    "bash",
                    str(ROOT / "install.sh"),
                    "-l",
                ],
                env,
            )
            for scheme in [[], ["--light"]]:
                result = self.run_program(
                    [sys.executable, str(ROOT / "tests/installed_gtk4.py"), *scheme],
                    env,
                )
                self.assertTrue(json.loads(result.stdout)["automatic_user_css"])
            self.run_program(
                ["bash", str(ROOT / "install.sh"), "--remove", "-l"],
                env,
            )
            self.assertFalse((home / "config/gtk-4.0/gtk.css").exists())

    def test_installed_extras_are_consumed_without_replacing_user_settings(self):
        with tempfile.TemporaryDirectory(prefix="amoled-extra-install-") as temporary:
            home = Path(temporary) / "home with space # % ü"
            home.mkdir()
            env = dict(
                os.environ,
                HOME=str(home),
                XDG_CONFIG_HOME=str(home / "config"),
                XDG_DATA_HOME=str(home / "data"),
                XDG_STATE_HOME=str(home / "state"),
                XDG_CACHE_HOME=str(home / "cache"),
                GSETTINGS_BACKEND="memory",
                NVIM_LOG_FILE=str(home / "nvim.log"),
            )
            for name in [
                "SUDO_USER",
                "ZDOTDIR",
                "NVIM_APPNAME",
                "BAT_CONFIG_PATH",
                "BAT_CACHE_PATH",
                "BAT_THEME",
                "KITTY_CONFIG_DIRECTORY",
                "GTK_THEME",
            ]:
                env.pop(name, None)
            env["XDG_CONFIG_DIRS"] = str(home / "empty-system-config")
            originals = {
                "bat/config": "--style=numbers\n--theme=Monokai\n",
                "kitty/kitty.conf": "font_size 14\n",
                "nvim/init.lua": "vim.o.number = true\n",
                "rofi/config.rasi": "configuration {show-icons: false;}\n",
                "alacritty/alacritty.toml": "[font]\nsize=14\n",
            }
            for name, text in originals.items():
                p = home / "config" / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            result = self.run_program(
                [
                    "bash",
                    str(ROOT / "install.sh"),
                    "--extras",
                    "all",
                ],
                env,
            )
            for name, text in originals.items():
                self.assertEqual((home / "config" / name).read_text(), text)
            kitty = home / "config/kitty/kitty.conf"
            with kitty.open("a") as stream:
                stream.write(
                    "include "
                    + str(home / "config/kitty/themes/adwaita-amoled.conf")
                    + "\n"
                )
            code = (
                "from kitty.config import load_config; c=load_config("
                + repr(str(kitty))
                + "); assert c.font_size==14; assert c.dim_opacity==0.75; assert c.tab_bar_min_tabs==2"
            )
            result = self.run_program(["kitty", "+runpy", code], env)
            self.assertNotIn("could not", result.stderr.lower())
            self.assertNotIn("ignoring", result.stderr.lower())
            bat = shutil.which("bat") or shutil.which("batcat")
            self.assertIsNotNone(bat)
            self.assertIn(
                "adwaita-amoled",
                self.run_program([bat, "--list-themes", "--color=never"], env).stdout,
            )
            self.assertIn(
                "\x1b[",
                self.run_program(
                    [
                        bat,
                        "--theme=adwaita-amoled",
                        "--color=always",
                        "--style=plain",
                        str(ROOT / "build.sh"),
                    ],
                    env,
                ).stdout,
            )
            self.run_program(
                [
                    "nvim",
                    "--headless",
                    "-i",
                    "NONE",
                    "-c",
                    "set termguicolors",
                    "-c",
                    "colorscheme adwaita-amoled",
                    "-c",
                    'lua assert(vim.g.colors_name=="adwaita-amoled"); assert(vim.o.number)',
                    "-c",
                    "qa!",
                ],
                env,
            )
            rofi = self.run_program(
                [
                    "rofi",
                    "-theme",
                    str(home / "config/rofi/themes/adwaita-amoled.rasi"),
                    "-dump-theme",
                ],
                env,
            )
            self.assertIn("element selected", rofi.stdout)
            self.assertNotIn("parser error", rofi.stderr.lower())
            self.run_program(
                [
                    "zsh",
                    "-f",
                    "-c",
                    'source "$XDG_CONFIG_HOME/zsh/adwaita-amoled.zsh"; [[ "$PROMPT" == *8ab4f8* ]]',
                ],
                env,
            )
            config = tomllib.loads(
                (home / "config/alacritty/alacritty.toml").read_text()
            )
            self.assertEqual(config["font"]["size"], 14)
            self.assertNotIn("general", config)
            self.assertIn(
                "colors",
                tomllib.loads(
                    (home / "config/alacritty/themes/adwaita-amoled.toml").read_text()
                ),
            )
            for qt in ["qt5ct", "qt6ct"]:
                self.assertEqual(
                    (home / f"config/{qt}/colors/Adwaita-AMOLED.conf").read_bytes(),
                    (ROOT / f"extra/{qt}/colors/Adwaita-AMOLED.conf").read_bytes(),
                )
            self.run_program(
                ["bash", str(ROOT / "install.sh"), "--remove", "--extras", "all"],
                env,
            )
            # The installer leaves the explicitly added test include alone.
            originals["kitty/kitty.conf"] += (
                "include "
                + str(home / "config/kitty/themes/adwaita-amoled.conf")
                + "\n"
            )
            for name, text in originals.items():
                self.assertEqual((home / "config" / name).read_text(), text)
            print(
                "Bash-installed app themes: Kitty, bat, Neovim, Rofi and Zsh loaded explicitly; Qt palettes and Alacritty TOML verified."
            )


if __name__ == "__main__":
    from report import main

    main()
