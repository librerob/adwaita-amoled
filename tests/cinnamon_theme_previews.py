"""Exercise Cinnamon Settings' real thumbnail lookup and chooser widgets."""
import builtins
import inspect
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if '--isolated-child' not in sys.argv:
    with tempfile.TemporaryDirectory(prefix='amoled-chooser-') as temporary:
        home = Path(temporary)
        env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / 'data'),
                   XDG_CONFIG_HOME=str(home / 'config'), XDG_CACHE_HOME=str(home / 'cache'),
                   XDG_CURRENT_DESKTOP='', GSETTINGS_BACKEND='memory')
        env.pop('GTK_THEME', None)
        result = subprocess.run([sys.executable, __file__, sys.argv[1], '--isolated-child'], env=env)
        raise SystemExit(result.returncode)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
builtins._ = lambda text: text
sys.path.extend(['/usr/share/cinnamon/cinnamon-settings', '/usr/share/cinnamon/cinnamon-settings/bin',
                 '/usr/share/cinnamon/cinnamon-settings/modules'])
import cs_themes

out = Path(sys.argv[1]);out.mkdir(parents=True, exist_ok=True)
module = object.__new__(cs_themes.Module)
parent = Path(os.environ['XDG_DATA_HOME']) / 'themes'
theme = parent / 'Adwaita-AMOLED'


class Chooser(cs_themes.PictureChooserButton):
    def __init__(self):
        self.loaded = []
        parameters = inspect.signature(cs_themes.PictureChooserButton.__init__).parameters
        sizing = {'button_picture_size': 100, 'menu_pictures_size': 100} if 'button_picture_size' in parameters else {'button_picture_width': 247, 'menu_picture_width': 247}
        super().__init__(num_cols=1, has_button_label=True, **sizing)

    def create_scaled_surface(self, path):
        surface = super().create_scaled_surface(path)
        assert surface is not None, path
        self.loaded.append(Path(path).resolve())
        return surface


for accent in ('blue', 'yellow', 'gold', 'purple', 'green', 'red', 'orange', 'pink'):
    result = subprocess.run(['bash', str(ROOT / 'install.sh'), '--accent', accent],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    window = Gtk.OffscreenWindow();module.window = window
    layout = Gtk.Box(spacing=12);layout.set_border_width(12);window.add(layout)
    for kind in ('metacity-1', 'gtk-3.0', 'cinnamon'):
        chooser = Chooser();layout.add(chooser)
        module.set_button_chooser(chooser, 'Adwaita-AMOLED', 'themes', kind, 100)
        module.refresh_chooser(chooser, kind, [('Adwaita-AMOLED', str(parent))], lambda *_: True)
        expected = (theme / kind / 'thumbnail.png').resolve()
        assert chooser.loaded.count(expected) == 2, (accent, kind, chooser.loaded)
        pix = GdkPixbuf.Pixbuf.new_from_file(str(expected))
        assert (pix.get_width(), pix.get_height()) == (247, 100)
    window.show_all()
    while Gtk.events_pending():Gtk.main_iteration()
    window.get_pixbuf().savev(str(out / (accent + '-chooser.png')), 'png', [], [])
    window.destroy()
    print(accent, 'all three native chooser previews loaded', flush=True)
