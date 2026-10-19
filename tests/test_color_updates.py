"""Independent icon choices and recoloring existing installed components."""
import hashlib
import os
from pathlib import Path
import shutil
import unittest

import test_installer as base

COLORS = ('blue', 'yellow', 'gold', 'purple', 'green', 'red', 'orange', 'pink')


class ColorUpdateTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    write = base.InstallerTests.write
    fake_program = base.InstallerTests.fake_program

    def expected(self, accent, name):
        overlay = base.ROOT / 'accents' / accent / name
        return overlay if accent != 'blue' and overlay.is_file() else base.ROOT / name

    def icons(self):
        return self.data / 'icons' / base.THEME

    def snapshot(self):
        return {str(p.relative_to(self.home)): ('link', os.readlink(p)) if p.is_symlink()
                else ('file', hashlib.sha256(p.read_bytes()).hexdigest()) if p.is_file()
                else ('directory', p.stat().st_mode)
                for p in self.home.rglob('*')}

    def test_all_64_theme_and_folder_color_combinations(self):
        for accent in COLORS:
            for icon in COLORS:
                with self.subTest(accent=accent, icons=icon):
                    self.run_cli('--accent', accent, '--icons', '--icon-accent', icon)
                    self.assertEqual((self.theme / 'gtk-3.0/gtk.gresource').read_bytes(),
                                     self.expected(accent, 'gtk-3.0/gtk.gresource').read_bytes())
                    self.assertEqual((self.theme / 'icon-accent').read_text(), icon + '\n')
                    self.assertEqual((self.icons() / 'accent-name').read_text(), icon + '\n')
                    for name in (self.icons() / 'runtime-files.txt').read_text().splitlines():
                        self.assertEqual((self.icons() / name).read_bytes(),
                                         self.expected(icon, 'extra/icons/Adwaita-AMOLED/' + name).read_bytes())

    def test_recolor_preserves_independent_choice_then_can_restore_matching(self):
        self.run_cli('--accent', 'pink', '--icons', '--icon-accent', 'yellow', '--extras', 'qt,kitty,nvim')
        # A single Qt installation and custom GTK4/app configuration must stay so.
        shutil.rmtree(self.config / 'qt6ct')
        self.write(self.config / 'gtk-4.0/gtk.css', '/* private override */\n')
        self.write(self.config / 'kitty/kitty.conf', 'font_size 15\n')
        self.write(self.config / 'nvim/init.lua', '-- personal settings\n')
        self.write(self.config / 'zsh/adwaita-amoled.zsh', 'old installed snippet\n')
        self.run_cli('--recolor', '--accent', 'green')
        self.assertEqual((self.theme / 'accent-name').read_text(), 'green\n')
        self.assertEqual((self.icons() / 'accent-name').read_text(), 'yellow\n')
        self.assertEqual((self.theme / 'icon-accent').read_text(), 'yellow\n')
        for installed, source in [
            ('qt5ct/colors/Adwaita-AMOLED.conf', 'qt5ct/colors/Adwaita-AMOLED.conf'),
            ('kitty/themes/adwaita-amoled.conf', 'kitty/adwaita-amoled.conf'),
            ('nvim/colors/adwaita-amoled.vim', 'nvim/colors/adwaita-amoled.vim'),
            ('zsh/adwaita-amoled.zsh', 'zsh/.zshrc'),
        ]:
            self.assertEqual((self.config / installed).read_bytes(), self.expected('green', 'extra/' + source).read_bytes())
        self.assertFalse((self.config / 'qt6ct').exists())
        self.assertFalse((self.config / 'alacritty').exists())
        self.assertEqual((self.config / 'gtk-4.0/gtk.css').read_text(), '/* private override */\n')
        self.assertEqual((self.config / 'kitty/kitty.conf').read_text(), 'font_size 15\n')
        self.assertEqual((self.config / 'nvim/init.lua').read_text(), '-- personal settings\n')
        before = self.snapshot()
        self.run_cli('--recolor', '--accent', 'blue', '--icon-accent', 'match', '--dry-run')
        self.assertEqual(self.snapshot(), before)
        self.run_cli('--recolor', '--icon-accent', 'match')
        self.assertEqual((self.icons() / 'accent-name').read_text(), 'green\n')
        self.run_cli('--recolor', '--accent', 'purple')
        self.assertEqual((self.icons() / 'accent-name').read_text(), 'purple\n')
        self.assertEqual((self.theme / 'icon-accent').read_text(), 'match\n')

    def test_recolor_does_not_install_missing_optional_components(self):
        result = self.run_cli('--recolor', success=False)
        self.assertIn('Install the theme first', result.stderr)
        self.assertFalse(self.theme.exists())
        self.run_cli()
        self.run_cli('--recolor', '--accent', 'gold')
        self.assertFalse(self.icons().exists())
        self.assertFalse(self.config.exists())
        self.assertEqual((self.theme / 'accent-name').read_text(), 'gold\n')
        self.run_cli('--recolor', '--remove', success=False)
        self.run_cli('--recolor', '-l', success=False)

    def test_corrupt_independent_icon_variant_stops_before_theme_changes(self):
        self.run_cli('--icons')
        before = self.snapshot()
        source = self.base / 'damaged-source'
        shutil.copytree(base.ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        (source / 'accents/pink/extra/icons/Adwaita-AMOLED/scalable/places/folder.svg').write_text('damaged')
        self.run_cli('--accent', 'green', '--icons', '--icon-accent', 'pink', root=source, success=False)
        self.assertEqual(self.snapshot(), before)
        self.run_cli('--icon-accent', 'not-a-preset', success=False)
        self.assertEqual(self.snapshot(), before)

    def test_cinnamon_reload_only_for_the_selected_live_user_theme(self):
        log = self.base / 'reload.log'
        self.env.update(XDG_CURRENT_DESKTOP='X-Cinnamon', DBUS_SESSION_BUS_ADDRESS='fixture-bus',
                        RELOAD_LOG=str(log), RELOAD_THEME=str(self.theme), SELECTED_THEME=base.THEME)
        self.fake_program('gsettings', '''case "$1:$2:$3" in
get:org.cinnamon.theme:name) printf "'%s'\\n" "$SELECTED_THEME" ;;
range:*) exit 1 ;;
*) exit 0 ;;
esac''')
        self.fake_program('gdbus', '''[[ -f $RELOAD_THEME/accent-name ]] || exit 9
printf '%s\\n' "$*" >> "$RELOAD_LOG"
[[ ${RELOAD_FAIL:-no} != yes ]]''')
        self.run_cli('--accent', 'pink')
        self.assertIn('org.Cinnamon.ReloadTheme --timeout 10', log.read_text())
        self.assertNotIn('Eval', log.read_text())
        before = log.read_text()
        self.run_cli('--recolor', '--accent', 'green', '--dry-run')
        self.assertEqual(log.read_text(), before)
        self.env['SELECTED_THEME'] = 'Other theme'
        self.run_cli('--recolor', '--accent', 'yellow')
        self.assertEqual(log.read_text(), before)
        self.env.update(SELECTED_THEME=base.THEME, RELOAD_FAIL='yes')
        result = self.run_cli('--recolor', '--accent', 'purple')
        self.assertIn('Reselect the desktop theme', result.stderr)
        self.assertEqual((self.theme / 'accent-name').read_text(), 'purple\n')
        before = log.read_text()
        self.run_cli('--remove')
        self.assertEqual(log.read_text(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
