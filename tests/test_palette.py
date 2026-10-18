"""Shared colors reach every toolkit without rewriting upstream or runtime code."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_palette as palette


class PaletteTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="amoled-palette-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(ROOT / "palette", self.root / "palette")

    def change(self, name, value):
        path = self.root / "palette/colors.json"
        data = json.loads(path.read_text())
        data["colors"][name] = value
        path.write_text(json.dumps(data))

    def test_presets_reject_missing_accent_roles_semantic_overrides_and_duplicates(
        self,
    ):
        path = self.root / "palette/accents.json"
        original = json.loads(path.read_text())
        for change in ("missing", "semantic", "malformed", "duplicate"):
            with self.subTest(change=change):
                data = json.loads(json.dumps(original))
                colors = data["presets"]["gold"]["colors"]
                if change == "missing":
                    colors.pop("accent_fill")
                elif change == "semantic":
                    colors["error_text"] = "#123456"
                elif change == "malformed":
                    colors["accent_fill"] = "gold"
                text = json.dumps(data)
                if change == "duplicate":
                    text = text.replace(
                        '"accent_fill":', '"accent_text": "#123456", "accent_fill":', 1
                    )
                path.write_text(text)
                with self.assertRaises(ValueError):
                    palette.preset_colors(self.root, "gold")

    def test_committed_outputs_match_templates_without_changes(self):
        self.assertEqual(palette.generate(ROOT, check=True), [])

    def test_nested_style_braces_and_case_formats_remain_valid(self):
        self.assertEqual(
            palette.render(
                "a { b { color: {{accent_text.upper}}; }}", {"accent_text": "#8ab4f8"}
            ),
            b"a { b { color: #8AB4F8; }}",
        )
        self.assertEqual(
            palette.render("#ff{{accent_text.hex_upper}}", {"accent_text": "#8ab4f8"}),
            b"#ff8AB4F8",
        )

    def test_color_change_reaches_css_sass_svg_qt_and_app_configs(self):
        self.change("accent_text", "#123456")
        palette.generate(self.root)
        for name, needle in {
            "src/gtk-3.0/gtk-main.css": "@define-color accent #123456;",
            "src/gtk-4.0/gtk-main.css": "@define-color accent_color             #123456;",
            "extra/libadwaita/gtk.css": "@define-color accent_color             #123456;",
            "gnome-shell/sass/gnome-shell-46.scss": "$link_color: #123456;",
            "cinnamon/cinnamon.css": "#123456",
            "gtk-2.0/gtkrc": "#123456",
            "extra/qt5ct/colors/Adwaita-AMOLED.conf": "#ff123456",
            "extra/qt6ct/colors/Adwaita-AMOLED.conf": "#ff123456",
            "extra/kitty/adwaita-amoled.conf": "#123456",
            "extra/nvim/colors/adwaita-amoled.vim": "guifg=#123456",
            "extra/zsh/.zshrc": "%F{#123456}",
        }.items():
            self.assertIn(needle, (self.root / name).read_text(), name)
        self.change("foreground", "#654321")
        palette.generate(self.root)
        self.assertIn(
            "#654321", (self.root / "src/gtk-4.0/assets/check-symbolic.svg").read_text()
        )
        # Channel placeholders preserve rgba syntax, alpha and original spacing.
        text = palette.render(
            "rgba({{accent_text.r}},{{accent_text.g}}, {{accent_text.b}},0.25)",
            {"accent_text": "#123456"},
        )
        self.assertEqual(text, b"rgba(18,52, 86,0.25)")

    def test_generation_is_repeatable_and_does_not_touch_upstream_or_binaries(self):
        protected = ["gnome-shell/sass/upstream/_colors.scss", "gtk-3.0/gtk.gresource"]
        for name in protected:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"untouched upstream or compiled output")
        palette.generate(self.root)
        self.assertEqual(palette.generate(self.root), [])
        for name in protected:
            self.assertEqual(
                (self.root / name).read_bytes(),
                b"untouched upstream or compiled output",
            )

    def test_check_detects_stale_output_without_writing(self):
        palette.generate(self.root)
        target = self.root / "extra/kitty/adwaita-amoled.conf"
        target.write_text("local stale edit")
        self.assertIn(
            Path("extra/kitty/adwaita-amoled.conf"),
            palette.generate(self.root, check=True),
        )
        self.assertEqual(target.read_text(), "local stale edit")
        palette.generate(self.root)
        self.assertEqual(
            target.read_bytes(), (ROOT / "extra/kitty/adwaita-amoled.conf").read_bytes()
        )

    def test_invalid_token_is_rejected_before_any_output_is_written(self):
        template = self.root / "palette/templates/src/invalid.css.in"
        template.write_text("color: {{not_a_color}};")
        with self.assertRaisesRegex(ValueError, "unknown palette token"):
            palette.generate(self.root)
        self.assertFalse((self.root / "cinnamon").exists())

    def test_invalid_values_duplicate_keys_and_placeholders_are_rejected(self):
        path = self.root / "palette/colors.json"
        for text in [
            '{"version":1,"colors":{"accent_text":"red"}}',
            '{"version":1,"colors":{"accent_text":"#8ab4f8","accent_text":"#123456"}}',
            '{"version":2,"colors":{"accent_text":"#8ab4f8"}}',
        ]:
            path.write_text(text)
            with self.assertRaises(ValueError):
                palette.generate(self.root)
        for text in ["{{accent_text.invalid}}", "{{bad-token}}", "{{accent_text"]:
            with self.assertRaises(ValueError):
                palette.render(text, {"accent_text": "#8ab4f8"})

    def test_templates_cannot_write_upstream_or_compiled_outputs(self):
        for name in [
            "gnome-shell/sass/upstream/example.scss",
            "gtk-4.0/gtk.gresource",
            "gnome-shell/gnome-shell-51.css",
            "gnome-shell/assets/example.svg",
        ]:
            with self.subTest(name=name):
                template = self.root / "palette/templates" / (name + ".in")
                template.parent.mkdir(parents=True, exist_ok=True)
                template.write_text("{{accent_text}}")
                with self.assertRaises(ValueError):
                    palette.generate(self.root)
                template.unlink()


if __name__ == "__main__":
    from report import main

    main()
