"""Check actual automatic user-CSS loading after running the installer."""

import argparse
import json
import time
import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, GLib
from gtk4_text import colors

parser = argparse.ArgumentParser()
parser.add_argument("--light", action="store_true")
args = parser.parse_args()
Adw.init()
Adw.StyleManager.get_default().set_color_scheme(
    Adw.ColorScheme.FORCE_LIGHT if args.light else Adw.ColorScheme.FORCE_DARK
)
window = Adw.Window()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
window.set_content(box)
window.set_default_size(480, 300)
widgets = {}
expected = {
    "accent": [138, 180, 248],
    "success": [143, 240, 164],
    "warning": [248, 228, 92],
    "error": [255, 123, 123],
}
for role in expected:
    label = Gtk.Label(label=role)
    label.add_css_class(role)
    box.append(label)
    widgets[role] = label
window.present()
end = time.monotonic() + 0.2
while time.monotonic() < end:
    while GLib.MainContext.default().pending():
        GLib.MainContext.default().iteration(False)
    time.sleep(0.002)
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 64, 64)
cr = cairo.Context(surface)
cr.set_source_rgb(1, 0, 1)
cr.paint()
Gtk.render_background(window.get_style_context(), cr, 0, 0, 64, 64)
surface.flush()
data = bytes(surface.get_data())
pixel = 32 * surface.get_stride() + 32 * 4
assert [data[pixel + n] for n in (2, 1, 0)] == [0, 0, 0]
resolved = {name: colors(widget) for name, widget in widgets.items()}
for role, rgb in expected.items():
    assert resolved[role], (role, "No native text colors were measured")
    assert all(
        foreground == rgb and alpha == 1 for foreground, alpha in resolved[role]
    ), (role, resolved[role])
window.destroy()
print(
    json.dumps(
        {
            "gtk_minor": Gtk.get_minor_version(),
            "adw_minor": Adw.get_minor_version(),
            "light": args.light,
            "automatic_user_css": True,
            "rendered_background": "#000000",
            "colors": resolved,
        }
    )
)
