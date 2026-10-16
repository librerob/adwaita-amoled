"""GNOME Shell 51 source checks and native headless rendering."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / 'gnome-shell'


def rules(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    return [(' '.join(selector.split()),
             [(key.strip(), value.strip()) for key, value in
              re.findall(r'([\w-]+)\s*:\s*([^;]+);', body)])
            for selector, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css)]


class ShellSourceTests(unittest.TestCase):
    def test_upstream_files_and_assets_match_recorded_source(self):
        metadata = json.loads((THEME / 'UPSTREAM.json').read_text())
        self.assertEqual(metadata['version'], '51.1')
        self.assertEqual(metadata['commit'], '33da06854e229c256afd5872fedd83c28cbfa176')
        for name, source in metadata['files'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((THEME / name).read_bytes()).hexdigest(), source['sha256'])

    def test_compiled_css_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'gnome-shell.css'
            subprocess.run(['bash', str(THEME / 'build.sh'), str(target)], check=True, capture_output=True)
            self.assertEqual(target.read_bytes(), (THEME / 'gnome-shell.css').read_bytes())

    def test_upstream_layout_and_states_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'stock.scss'
            includes = '\n'.join(f'@import "{THEME / "sass/upstream" / name}";'
                                 for name in ('colors', 'drawing', 'common', 'widgets'))
            source.write_text("$variant: 'dark';\n$contrast: 'normal';\n" + includes)
            result = subprocess.run(['sassc', '-t', 'expanded', str(source)],
                                    check=True, capture_output=True, text=True)
        stock = rules(result.stdout)
        amoled = rules((THEME / 'gnome-shell.css').read_text())
        self.assertGreater(len(stock), 900)
        self.assertEqual(len(stock), len(amoled))
        color_properties = {'color', 'background', 'background-color', 'background-image',
                            'border', 'border-color', 'box-shadow', '-arrow-background-color',
                            '-arrow-border-color', '-barlevel-overdrive-color', 'warning-color'}
        for (selector, before), (new_selector, after) in zip(stock, amoled):
            self.assertEqual(selector, new_selector)
            self.assertEqual([key for key, _ in before], [key for key, _ in after], selector)
            for (key, value), (_, new_value) in zip(before, after):
                if key not in color_properties:
                    self.assertEqual(value, new_value, f'{selector}: {key}')
                elif key == 'border':
                    color = r'(?=#[\da-fA-F]+\b|(?:rgba?|hsla?|st-[\w-]+)\(|\b(?:transparent|currentColor|black|white)\b)'
                    self.assertEqual(re.split(color, value, maxsplit=1)[0].strip(),
                                     re.split(color, new_value, maxsplit=1)[0].strip(), selector)


class ShellRuntimeTests(unittest.TestCase):
    def test_native_shell_theme_and_rendering(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(os.environ.get('THEME_TEST_OUTPUT', temporary))
            output.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ, THEME_TEST_OUTPUT=str(output),
                       META_DBUS_RUNNER_DISABLE_LOGIND_PASSTHROUGH='1',
                       PYTHONDONTWRITEBYTECODE='1', G_DEBUG='fatal-criticals')
            with (output / 'shell-session.log').open('w') as log:
                process = subprocess.Popen([sys.executable, str(ROOT / 'tests/gnome-shell/dbus_runner.py'),
                                            '--', 'bash', str(ROOT / 'tests/gnome-shell/session.sh')],
                                           env=env, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                try:
                    status = process.wait(timeout=120)
                finally:
                    # Stop only this fixture's process group, including test services.
                    import signal
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
            log = (output / 'shell-session.log').read_text()
            self.assertEqual(status, 0, log)
            self.assertNotRegex(log,
                                r'Theme parsing error|Failed to parse stylesheet|Error loading.*assets/')
            self.assertIn('AMOLED_SHELL_RESULT ', log, log)
            result = json.loads((output / 'shell-results.json').read_text())
            self.assertEqual(len(result['views']), 8)
            self.assertEqual(result['transitions'], 40)
            self.assertGreater(result['styleNodes'], 1000)
            for name in result['views']:
                self.assertGreater((output / f'shell-{name}.png').stat().st_size, 100)
            print(json.dumps(result))


if __name__ == '__main__':
    from report import main
    main()
