"""Resolve real libadwaita widget colors in both requested color schemes."""
import argparse
import json
from pathlib import Path
import time

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, GLib, Gtk

from test_theme import contrast

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--light', action='store_true')
parser.add_argument('--stylesheet', type=Path, help='Override the entry point for before/after comparisons')
args = parser.parse_args()
Adw.init()
Adw.StyleManager.get_default().set_color_scheme(
    Adw.ColorScheme.FORCE_LIGHT if args.light else Adw.ColorScheme.FORCE_DARK)
modern = (Gtk.get_major_version(), Gtk.get_minor_version()) >= (4, 16)
stylesheet = args.stylesheet or ROOT / 'extra/libadwaita' / ('gtk-modern.css' if modern else 'gtk.css')
errors = []
provider = Gtk.CssProvider()
provider.connect('parsing-error', lambda _p, _s, error: errors.append(str(error)))
provider.load_from_path(str(stylesheet))
assert not errors, errors
Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                          Gtk.STYLE_PROVIDER_PRIORITY_USER)
window = Adw.Window()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
window.set_content(box)
widgets = {}
for css in ('accent', 'success', 'warning', 'error'):
    label = Gtk.Label(label=css)
    label.add_css_class(css)
    box.append(label)
    widgets[css] = (label, css + '_color')
if (Adw.get_major_version(), Adw.get_minor_version()) >= (1, 6):
    button = Gtk.Button(label='Destructive action')
    button.add_css_class('destructive-action')
    box.append(button)
    widgets['destructive-action'] = (button, 'destructive_color')
window.present()
context = GLib.MainContext.default()
end = time.monotonic() + .15
while time.monotonic() < end:
    while context.pending():
        context.iteration(False)
    time.sleep(.002)

def hex_color(color):
    return '#' + ''.join(f'{max(0, min(255, round(channel * 255))):02x}'
                         for channel in (color.red, color.green, color.blue))

found, background = window.get_style_context().lookup_color('window_bg_color')
assert found and hex_color(background) == '#000000'
resolved = {}
for name, (widget, color_name) in widgets.items():
    style = widget.get_style_context()
    found, expected = style.lookup_color(color_name)
    assert found, color_name
    actual = style.get_color()
    foreground = hex_color(actual)
    ratio = contrast(foreground, hex_color(background))
    resolved[name] = {'foreground': foreground, 'contrast_on_window': ratio}
    assert ratio >= 4.5, f'{name} text has only {ratio:.2f}:1 contrast: {foreground} on #000000'
    assert foreground == hex_color(expected), (name, foreground, hex_color(expected))
window.destroy()
print(json.dumps({'gtk_minor': Gtk.get_minor_version(), 'adwaita_minor': Adw.get_minor_version(),
                  'light_preference': args.light, 'stylesheet': stylesheet.name,
                  'colors': resolved, 'parser_errors': errors}))
