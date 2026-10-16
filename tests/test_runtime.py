"""Run under xvfb-run; these checks require the native libraries in tests/README.md."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RuntimeTests(unittest.TestCase):
    def check_native(self, *args, script='native.py'):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            (data / 'themes').mkdir()
            (data / 'themes/Adwaita-AMOLED').symlink_to(ROOT, target_is_directory=True)
            env = dict(os.environ, XDG_DATA_HOME=str(data), XDG_CONFIG_HOME=str(data / 'config'),
                       GSETTINGS_BACKEND='memory', GSK_RENDERER='cairo', G_DEBUG='fatal-criticals')
            result = subprocess.run([sys.executable, str(ROOT / 'tests' / script), *args],
                                    env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('Theme parsing error', result.stderr)
            print(result.stdout.strip())

    def test_gtk3(self):
        self.check_native('3.0')

    def test_gtk4(self):
        self.check_native('4.0')

    def test_libadwaita(self):
        self.check_native('4.0', '--adw')

    def test_libadwaita_dark_semantic_colors(self):
        self.check_native(script='adwaita_colors.py')

    def test_libadwaita_light_semantic_colors(self):
        self.check_native('--light', script='adwaita_colors.py')

    def test_metacity_renderer(self):
        self.check_native('--metacity')


if __name__ == '__main__':
    from report import main
    main()
