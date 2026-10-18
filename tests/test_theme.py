"""Source/bundle, installation and extra-config regression tests."""
import configparser
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, timeout=60, **kwargs)


def contrast(foreground, background):
    def luminance(color):
        rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + .05) / (low + .05)


class ThemeTests(unittest.TestCase):
    def test_bundled_resources_match_sources_and_rebuild(self):
        for version in ('3.0', '4.0'):
            with self.subTest(gtk=version), tempfile.TemporaryDirectory() as temporary:
                source = ROOT / f'src/gtk-{version}'
                manifest = source / f'adwaita-amoled-gtk{version[0]}.gresource.xml'
                rebuilt = Path(temporary) / 'gtk.gresource'
                result = run('glib-compile-resources', str(manifest), '--sourcedir=' + str(source),
                             '--target=' + str(rebuilt))
                self.assertEqual(result.returncode, 0, result.stderr)
                expected = {}
                for group in ET.parse(manifest).getroot():
                    for entry in group:
                        expected[group.attrib['prefix'] + '/' + entry.get('alias', entry.text)] = (
                            source / entry.text).read_bytes()
                # Validate both shipping and freshly built bundles. Compression may differ
                # between toolchain versions; the extracted contents must be identical.
                for bundle in (ROOT / f'gtk-{version}/gtk.gresource', rebuilt):
                    paths = run('gresource', 'list', str(bundle))
                    self.assertEqual(paths.returncode, 0, paths.stderr)
                    self.assertEqual(set(paths.stdout.splitlines()), set(expected))
                    for path, data in expected.items():
                        extracted = subprocess.run(['gresource', 'extract', str(bundle), path],
                                                   capture_output=True, timeout=30, check=True)
                        self.assertEqual(extracted.stdout, data, path)

    def test_stylesheet_asset_paths_exist(self):
        for path in ROOT.rglob('*'):
            if path.suffix not in ('.css', '.qss', '.rasi'):
                continue
            text = re.sub(r'/\*.*?\*/', '', path.read_text(), flags=re.S)
            for match in re.finditer(r'''url\(\s*['"]?([^)'"\s]+)['"]?\s*\)''', text):
                url = match[1]
                if not re.match(r'(resource|data|https?):', url):
                    candidates = [path.parent / url]
                    if path.is_relative_to(ROOT / 'accents'):
                        # Sparse overlays inherit unchanged assets from the base.
                        relative = path.relative_to(ROOT / 'accents').parts[1:]
                        candidates.append((ROOT / Path(*relative)).parent / url)
                    self.assertTrue(any(p.is_file() for p in candidates), f'{path}: {url}')

    def test_svg_ids_and_references(self):
        for path in ROOT.rglob('*.svg'):
            tree = ET.parse(path)
            ids = [e.attrib['id'] for e in tree.iter() if 'id' in e.attrib]
            self.assertEqual(len(ids), len(set(ids)), str(path))
            for element in tree.iter():
                # Inline CSS overrides SVG presentation attributes. Upstream
                # Shell artwork retains old fill URLs beneath valid style fills.
                inline = dict(re.findall(r'([\w-]+)\s*:\s*([^;]+)',
                                         element.get('style', '')))
                for attribute, value in element.attrib.items():
                    if attribute != 'style' and attribute in inline:
                        continue
                    references = re.findall(r'''url\(\s*['"]?#([^)'"\s]+)['"]?\s*\)''', value)
                    if attribute.rsplit('}', 1)[-1] == 'href' and value.startswith('#'):
                        references.append(value[1:])
                    for reference in references:
                        self.assertIn(reference, ids, str(path))

    def test_selected_text_contrast(self):
        nvim = (ROOT / 'extra/nvim/colors/adwaita-amoled.vim').read_text()
        checked = 0
        for line in nvim.splitlines():
            match = re.match(r'hi\s+(\S+)\s+guifg=(#[\da-f]{6})\s+guibg=(#[\da-f]{6})', line)
            if match:
                checked += 1
                self.assertGreaterEqual(contrast(match[2], match[3]), 4.5, match[1])
        self.assertGreater(checked, 10, 'Expected explicit Neovim foreground/background pairs')
        alacritty = tomllib.loads((ROOT / 'extra/alacritty/alacritty.toml').read_text())
        focused = alacritty['colors']['search']['focused_match']
        self.assertGreaterEqual(contrast(focused['foreground'], focused['background']), 4.5)
        kitty = dict(line.split(None, 1) for line in (ROOT / 'extra/kitty/adwaita-amoled.conf').read_text().splitlines()
                     if line and not line.startswith('#'))
        self.assertGreaterEqual(contrast(kitty['active_tab_foreground'], kitty['active_tab_background']), 4.5)
        for name in ('src/gtk-4.0/gtk-main.css', 'extra/libadwaita/gtk.css', 'extra/libadwaita/gtk-dark.css'):
            text = (ROOT / name).read_text()
            bg = re.search(r'@define-color accent_bg_color\s+(#[\da-f]{6});', text)[1]
            fg = re.search(r'@define-color accent_fg_color\s+(#[\da-f]{6});', text)[1]
            self.assertGreaterEqual(contrast(fg, bg), 4.5, name)
        rasi = (ROOT / 'extra/rofi/adwaita-dark.rasi').read_text()
        selected = re.search(r'element selected\s*\{(.*?)\}', rasi, re.S)[1]
        fg = re.search(r'text-color:\s*(#[\da-f]{6});', selected)[1]
        bg = re.search(r'background-color:\s*(#[\da-f]{6});', selected)[1]
        self.assertGreaterEqual(contrast(fg, bg), 4.5)
        gtk2 = (ROOT / 'gtk-2.0/gtkrc').read_text()
        fg = re.search(r'selected_fg_color:(#[\da-f]{6})', gtk2)[1]
        bg = re.search(r'selected_bg_color:(#[\da-f]{6})', gtk2)[1]
        self.assertGreaterEqual(contrast(fg, bg), 4.5)
        for qt in ('qt5ct', 'qt6ct'):
            config = configparser.ConfigParser()
            config.read(ROOT / f'extra/{qt}/colors/Adwaita-AMOLED.conf')
            for group in ('active_colors', 'inactive_colors', 'disabled_colors'):
                colors = [v.strip() for v in config['ColorScheme'][group].split(',')]
                self.assertEqual(len(colors), 21)
                self.assertTrue(all(re.fullmatch(r'#[\da-f]{8}', v) for v in colors))
                if group != 'disabled_colors':
                    # QPalette::Highlight and HighlightedText, stripping opaque ARGB alpha.
                    self.assertGreaterEqual(contrast('#' + colors[13][3:], '#' + colors[12][3:]), 4.5)

    def test_success_color_pair_contrast(self):
        pairs = []
        for name in ('src/gtk-4.0/gtk-main.css', 'extra/libadwaita/gtk.css', 'extra/libadwaita/gtk-dark.css'):
            with self.subTest(stylesheet=name):
                text = (ROOT / name).read_text()
                bg = re.search(r'@define-color success_bg_color\s+(#[\da-f]{6});', text)[1]
                fg = re.search(r'@define-color success_fg_color\s+(#[\da-f]{6});', text)[1]
                pairs.append((fg, bg))
                self.assertGreaterEqual(contrast(fg, bg), 4.5, name)
        self.assertEqual(len(set(pairs)), 1, 'Theme and user overrides must use the same success colors')

    def test_secondary_editor_text_contrast(self):
        text = (ROOT / 'extra/nvim/autoload/airline/themes/adwaita_amoled.vim').read_text()
        foreground = re.search(r"let s:ghost\s*=\s*\['(#[\da-f]{6})'", text)[1]
        background = re.search(r"let s:surface\s*=\s*\['(#[\da-f]{6})'", text)[1]
        self.assertGreaterEqual(contrast(foreground, background), 4.5, 'Airline filename and inactive text')

    def test_openbox_title_text_contrast(self):
        values = {}
        for line in (ROOT / 'openbox-3/themerc').read_text().splitlines():
            if ':' in line and not line.lstrip().startswith('!'):
                name, value = line.split(':', 1)
                values[name.strip()] = value.strip()
        for state in ('active', 'inactive'):
            with self.subTest(state=state):
                foreground = values[f'window.{state}.label.text.color']
                background = values[f'window.{state}.title.bg.color']
                self.assertGreaterEqual(contrast(foreground, background), 4.5, state + ' title')

    def test_zsh_clean_shell_and_existing_hooks(self):
        with tempfile.TemporaryDirectory() as temporary:
            completions = Path(temporary) / 'completions'
            completions.mkdir()
            completions.chmod(0o777)
            env = dict(os.environ, THEME_ROOT=str(ROOT), ZDOTDIR=temporary,
                       THEME_TEST_COMPLETIONS=str(completions))
            result = run('zsh', '-f', '-c', '''
                fpath=( "$THEME_TEST_COMPLETIONS" $fpath )
                precmd() { print -r -- existing-hook; }
                source "$THEME_ROOT/extra/zsh/.zshrc" || exit 1
                source "$THEME_ROOT/extra/zsh/.zshrc" || exit 1
                [[ ${(t)FAST_HIGHLIGHT_STYLES} == association* ]] || exit 2
                [[ ${#precmd_functions} == 1 ]] || exit 3
                [[ $(precmd) == existing-hook ]] || exit 4
                _adwaita_amoled_title
            ''', env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertIn('\x1b]0;', result.stdout)
            for placeholder in ('%n', '%m', '%~'):
                self.assertNotIn(placeholder, result.stdout)
            self.assertTrue(result.stdout.endswith('\x07'))

    def test_kitty_native_config(self):
        path = str(ROOT / 'extra/kitty/adwaita-amoled.conf')
        code = 'from kitty.config import load_config; assert load_config(' + repr(path) + ').dim_opacity == 0.75'
        result = run('kitty', '+runpy', code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('unknown config', result.stderr.lower())
        self.assertNotIn('ignoring', result.stderr.lower())

    def test_zsh_preserves_interactive_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ, THEME_ROOT=str(ROOT), ZDOTDIR=temporary)
            result = run('zsh', '-f', '-i', '+m', '-c', '''
                compdef() { print -r -- existing-completion; }
                source "$THEME_ROOT/extra/zsh/.zshrc" || exit 1
                [[ $(compdef) == existing-completion ]] || exit 2
            ''', env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')

    def test_neovim_colorscheme(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ, THEME_ROOT=str(ROOT), NVIM_LOG_FILE=temporary + '/nvim.log')
            result = run('nvim', '--headless', '-u', 'NONE', '-i', 'NONE', '-c',
                         'lua dofile(vim.env.THEME_ROOT .. "/tests/nvim.lua")', env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('E5113', result.stderr)

    def test_install_uses_xdg_paths_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / 'checkout'
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            env = dict(os.environ, HOME=str(base / 'home'), XDG_DATA_HOME=str(base / 'data'),
                       XDG_CONFIG_HOME=str(base / 'config'), XDG_STATE_HOME=str(base / 'state'),
                       XDG_CACHE_HOME=str(base / 'cache'))
            env.pop('SUDO_USER', None)
            for _ in range(2):
                result = run('bash', str(source / 'build.sh'), '--install', '-l', '--gtk4-mode', 'legacy', env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = base / 'data/themes/Adwaita-AMOLED'
            self.assertFalse((installed / 'src').exists())
            self.assertEqual((base / 'config/gtk-4.0/gtk.css').resolve(),
                             installed / 'extra/libadwaita/gtk.css')
            for version in ('3.0', '4.0'):
                self.assertEqual((installed / f'gtk-{version}/gtk.gresource').read_bytes(),
                                 (source / f'gtk-{version}/gtk.gresource').read_bytes())



if __name__ == '__main__':
    from report import main
    main()
