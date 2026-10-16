"""Contrast of shipped color roles, including compositing and non-text cues."""

import configparser
from pathlib import Path
import plistlib
import re
import tomllib
import unittest
import xml.etree.ElementTree as ET

from test_theme import contrast

ROOT = Path(__file__).resolve().parents[1]


def composite(foreground, background, alpha):
    return "#" + "".join(
        f"{round(int(foreground[i:i+2], 16) * alpha + int(background[i:i+2], 16) * (1-alpha)):02x}"
        for i in (1, 3, 5)
    )


def kitty_config():
    return dict(
        line.split(None, 1)
        for line in (ROOT / "extra/kitty/adwaita-amoled.conf").read_text().splitlines()
        if line and not line.startswith("#")
    )


class ReadabilityTests(unittest.TestCase):
    def pair(self, foreground, background, name, minimum=4.5):
        with self.subTest(role=name, foreground=foreground, background=background):
            self.assertGreaterEqual(contrast(foreground, background), minimum, name)

    def test_alacritty_text_cursor_selection_and_faint_palette(self):
        colors = tomllib.loads((ROOT / "extra/alacritty/alacritty.toml").read_text())[
            "colors"
        ]
        for role, fg, bg in [
            ("primary", "foreground", "background"),
            ("cursor", "text", "cursor"),
            ("vi_mode_cursor", "text", "cursor"),
            ("selection", "text", "background"),
            ("footer_bar", "foreground", "background"),
        ]:
            self.pair(colors[role][fg], colors[role][bg], role)
        for role, data in colors["search"].items():
            self.pair(data["foreground"], data["background"], "search " + role)
        for group in ["normal", "bright", "dim"]:
            for name, color in colors[group].items():
                if name == "black" and group != "bright":
                    continue  # ANSI black is also an intentional background color.
                self.pair(color, colors["primary"]["background"], group + " " + name)

    def test_kitty_text_tabs_selection_and_faint_palette(self):
        colors = kitty_config()
        for fg, bg in [
            ("foreground", "background"),
            ("cursor_text_color", "cursor"),
            ("selection_foreground", "selection_background"),
            ("active_tab_foreground", "active_tab_background"),
            ("inactive_tab_foreground", "inactive_tab_background"),
        ]:
            self.pair(colors[fg], colors[bg], fg)
        for number in range(1, 16):
            color = colors[f"color{number}"]
            self.pair(color, colors["background"], f"ANSI {number}")
            self.pair(
                composite(color, colors["background"], float(colors["dim_opacity"])),
                colors["background"],
                f"faint ANSI {number}",
            )
        self.assertNotIn("fmt.fg.red", colors["tab_title_template"])

    def test_bat_syntax_over_normal_line_and_selection_backgrounds(self):
        document = plistlib.loads(
            (ROOT / "extra/bat/themes/adwaita-amoled.tmTheme").read_bytes()
        )
        defaults = document["settings"][0]["settings"]
        for item in document["settings"]:
            settings = item["settings"]
            if "foreground" not in settings:
                continue
            for bg in ["background", "lineHighlight", "selection"]:
                self.pair(
                    settings["foreground"],
                    defaults[bg],
                    item.get("name", "normal") + " on " + bg,
                )
        self.pair(
            defaults["findHighlightForeground"], defaults["findHighlight"], "search"
        )

    def test_qt_enabled_text_roles_and_links(self):
        for version in ["qt5ct", "qt6ct"]:
            c = configparser.ConfigParser()
            c.read(ROOT / f"extra/{version}/colors/Adwaita-AMOLED.conf")
            for group in ["active_colors", "inactive_colors"]:
                colors = [v.strip() for v in c["ColorScheme"][group].split(",")]

                def rgb(index):
                    return "#" + colors[index][3:]

                for fg, bg, name in [
                    (0, 10, "window"),
                    (6, 9, "view"),
                    (6, 16, "alternate view"),
                    (8, 1, "button"),
                    (13, 12, "highlight"),
                    (19, 18, "tooltip"),
                    (14, 9, "link"),
                    (15, 9, "visited link"),
                ]:
                    self.pair(rgb(fg), rgb(bg), version + " " + group + " " + name)
                self.pair(
                    composite(rgb(20), rgb(9), int(colors[20][1:3], 16) / 255),
                    rgb(9),
                    version + " " + group + " placeholder",
                )

    def test_openbox_enabled_labels_and_actionable_buttons(self):
        values = {}
        for line in (ROOT / "openbox-3/themerc").read_text().splitlines():
            if ":" in line and not line.lstrip().startswith("!"):
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
        for role in ["menu.title", "menu.items", "menu.items.active"]:
            self.pair(values[role + ".text.color"], values[role + ".bg.color"], role)
        for state in ["active", "inactive"]:
            self.pair(
                values[f"window.{state}.label.text.color"],
                values[f"window.{state}.title.bg.color"],
                state + " title",
            )
            self.pair(
                values[f"window.{state}.button.*.image.color"],
                values[f"window.{state}.title.bg.color"],
                state + " button",
                3,
            )

    def test_qt_scrollbar_handle_remains_visible(self):
        for qt in ["qt5ct", "qt6ct"]:
            source = (ROOT / f"extra/{qt}/qss/fusion-simple-scrollbar.qss").read_text()
            for red, green, blue, alpha in re.findall(
                r"background:\s*rgba\((\d+),\s*(\d+),\s*(\d+),\s*([.\d]+)\)", source
            ):
                foreground = "#" + "".join(
                    f"{int(value):02x}" for value in [red, green, blue]
                )
                for background in ["#000000", "#141414", "#333333"]:
                    self.pair(
                        composite(foreground, background, float(alpha)),
                        background,
                        qt + " scrollbar",
                        3,
                    )

    def test_zsh_completion_pairs_use_terminal_palette(self):
        colors = kitty_config()
        source = (ROOT / "extra/zsh/.zshrc").read_text()
        for name, codes in re.findall(r"'([a-z]+)=([\d;]+)'", source):
            codes = [int(v) for v in codes.split(";")]
            fg = bg = None
            bold = 1 in codes
            for code in codes:
                if 30 <= code <= 37:
                    index = code - 30 + (8 if bold else 0)
                    fg = colors[f"color{index}"]
                elif 40 <= code <= 47:
                    bg = colors[f"color{code-40}"]
            if fg and bg:
                self.pair(fg, bg, "completion " + name)
        for color in re.findall(r"fg=(#[\da-f]{6})", source):
            self.pair(color, colors["background"], "shell text")

    def test_cinnamon_control_paints_have_identifying_contrast(self):
        for name, property_name, background in [
            ("dark-assets/checkbox/checkbox-unchecked.svg", "stroke", "#262626"),
            ("dark-assets/checkbox/radio-unchecked.svg", "stroke", "#262626"),
            ("dark-assets/switch/switch-off.svg", "fill", "#141414"),
            ("common-assets/misc/add-workspace-active.svg", "fill", "#ffffff"),
        ]:
            root = ET.parse(ROOT / "cinnamon" / name).getroot()
            paints = set()
            for element in root.iter():
                style = dict(re.findall(r"([\w-]+):([^;]+)", element.get("style", "")))
                value = element.get(property_name, style.get(property_name))
                if value:
                    paints.add(value)
            expected = "#2d6be0" if "workspace" in name else "#808080"
            self.assertIn(expected, paints, name)
            self.pair(expected, background, name, 3)

    def test_gtk2_accent_roles_preserve_white_on_dark_fills(self):
        source = (ROOT / "gtk-2.0/gtkrc").read_text()
        for property_name in ["link-color", "visited-link-color"]:
            color = re.search(property_name + r'\s*=\s*"(#[\da-f]{6})"', source)[1]
            self.pair(color, "#1a1a1a", property_name, 7)
        for style in ["scrollbar", "scale"]:
            body = re.search('style "' + style + r'".*?\{(.*?)\n\}', source, re.S)[1]
            for color in re.findall(
                r'bg\[(?:ACTIVE|PRELIGHT)\]\s*=\s*"(#[\da-f]{6})"', body
            ):
                self.pair("#ffffff", color, style + " foreground")
                self.pair(color, "#000000", style + " indicator", 3)

    def test_standalone_accent_has_enhanced_contrast_on_theme_surfaces(self):
        for name in [
            "src/gtk-4.0/gtk-main.css",
            "extra/libadwaita/gtk.css",
            "extra/libadwaita/gtk-dark.css",
        ]:
            text = (ROOT / name).read_text()
            accent = re.search(r"@define-color accent_color\s+(#[\da-f]{6});", text)[1]
            for background in [
                "#000000",
                "#0f0f0f",
                "#141414",
                "#1a1a1a",
                "#252525",
                "#111820",
            ]:
                self.pair(accent, background, name + " standalone accent", 7)


if __name__ == "__main__":
    from report import main

    main()
