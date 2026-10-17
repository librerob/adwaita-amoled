"""Render actual GTK controls to separate subtle decoration from identifying edges."""

import argparse
import json
from pathlib import Path
import time
import cairo
import gi

parser = argparse.ArgumentParser()
parser.add_argument("version", choices=["3.0", "4.0"])
parser.add_argument("output", type=Path)
parser.add_argument("--record-only", action="store_true")
args = parser.parse_args()
gi.require_version("Gtk", args.version)
from gi.repository import Gtk, GLib

Gtk.init([]) if args.version == "3.0" else Gtk.init()
Gtk.Settings.get_default().set_property("gtk-theme-name", "Adwaita-AMOLED")
window = Gtk.Window()
window.set_default_size(900, 520)
window.set_title("AMOLED decorative border regression")
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
if args.version == "3.0":
    box.set_border_width(16)
    window.add(box)
else:
    for edge in ["top", "bottom", "start", "end"]:
        getattr(box, "set_margin_" + edge)(16)
    window.set_child(box)


def append(parent, child):
    (
        parent.pack_start(child, False, False, 0)
        if args.version == "3.0"
        else parent.append(child)
    )


def child(parent, content):
    parent.add(content) if args.version == "3.0" else parent.set_child(content)


header = Gtk.HeaderBar()
(
    header.set_title("Software Manager / Nemo border roles")
    if args.version == "3.0"
    else header.set_title_widget(
        Gtk.Label(label="Software Manager / Nemo border roles")
    )
)
append(box, header)
toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
toolbar.get_style_context().add_class("location-bar")
append(box, toolbar)
back = Gtk.Button(label="Back")
entry = Gtk.Entry()
entry.set_text("Search or location")
append(toolbar, back)
append(toolbar, entry)
grid = Gtk.Grid(column_spacing=12, row_spacing=12)
append(box, grid)
cards = []
for i, name in enumerate(
    ["Blender", "OBS Studio", "Spotify", "Discord", "Bitwarden", "Inkscape"]
):
    card = Gtk.Button()
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    append(content, Gtk.Label(label=name))
    append(content, Gtk.Label(label="Application description • Flathub"))
    child(card, content)
    card.set_size_request(260, 85)
    grid.attach(card, i % 3, i // 3, 1, 1)
    cards.append(card)
append(box, Gtk.CheckButton(label="Checkbox edges and focus remain identifiable"))
if args.version == "3.0":
    window.show_all()
else:
    window.present()
window.set_focus(None)


def settle():
    end = time.monotonic() + 0.25
    while time.monotonic() < end:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(0.005)


def edge(widget, state):
    widget.set_state_flags(state, True)
    settle()
    context = widget.get_style_context()
    widths = (
        context.get_border(state) if args.version == "3.0" else context.get_border()
    )
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 80, 48)
    cr = cairo.Context(surface)
    cr.set_source_rgb(0, 0, 0)
    cr.paint()
    Gtk.render_background(context, cr, 0, 0, 80, 48)
    surface.flush()
    data = bytes(surface.get_data())
    center = 24 * surface.get_stride() + 40 * 4
    background = [data[center + channel] for channel in (2, 1, 0)]
    cr.set_operator(cairo.OPERATOR_CLEAR)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)
    Gtk.render_frame(context, cr, 0, 0, 80, 48)
    surface.flush()
    raw = bytes(surface.get_data())
    positions = []
    for width, x, y in [
        (widths.top, 40, 0),
        (widths.bottom, 40, 47),
        (widths.left, 0, 24),
        (widths.right, 79, 24),
    ]:
        if width > 0:
            offset = y * surface.get_stride() + x * 4
            positions.append(
                [raw[offset + 2], raw[offset + 1], raw[offset], raw[offset + 3]]
            )
    return positions, background


def contrast(a, b):
    def luminance(rgb):
        c = [v / 255 for v in rgb]
        c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return sum(v * w for v, w in zip(c, [0.2126, 0.7152, 0.0722]))

    x, y = sorted([luminance(a), luminance(b)])
    return (y + 0.05) / (x + 0.05)


settle()
records = []
for name, widget, role in [
    ("package-card", cards[0], "decorative"),
    ("toolbar-button", back, "decorative"),
    ("headerbar", header, "decorative"),
    ("location-bar", toolbar, "decorative"),
    ("entry", entry, "identifying"),
]:
    for state_name, state in [
        ("normal", Gtk.StateFlags.NORMAL),
        ("hover", Gtk.StateFlags.PRELIGHT),
        ("backdrop", Gtk.StateFlags.BACKDROP),
    ]:
        pixels, background = edge(widget, state)
        records.append(
            {
                "name": name,
                "role": role,
                "state": state_name,
                "edge_pixels": pixels,
                "background": background,
            }
        )
        if not args.record_only:
            if role == "decorative":
                assert all(max(p[:3]) <= 64 for p in pixels), records[-1]
            else:
                ratios = [
                    contrast(
                        [p[i] + background[i] * (1 - p[3] / 255) for i in range(3)],
                        background,
                    )
                    for p in pixels
                ]
                assert ratios and min(ratios) >= 3, records[-1]
    widget.set_state_flags(Gtk.StateFlags.NORMAL, True)
settle()
if args.version == "3.0":
    cards[0].set_state_flags(Gtk.StateFlags.FOCUSED, True)
    settle()
    context = cards[0].get_style_context()
    ink = context.get_property("outline-color", Gtk.StateFlags.FOCUSED)
    rgb = [round(c * 255) for c in [ink.red, ink.green, ink.blue]]
    width = context.get_property("outline-width", Gtk.StateFlags.FOCUSED)
    assert width > 0 and contrast(rgb, [26, 26, 26]) >= 3, (rgb, width)
    records.append({"name": "keyboard-focus", "foreground": rgb, "width": width})
    cards[0].set_state_flags(Gtk.StateFlags.NORMAL, True)
    settle()
args.output.mkdir(parents=True, exist_ok=True)
(args.output / f"borders-{args.version}.json").write_text(
    json.dumps(records, indent=2) + "\n"
)
if args.version == "3.0":
    from gi.repository import Gdk

    allocation = window.get_allocation()
    image = Gdk.pixbuf_get_from_window(
        window.get_window(), 0, 0, allocation.width, allocation.height
    )
    image.savev(str(args.output / "border-gallery-gtk3.png"), "png", [], [])
window.destroy()
print(json.dumps(records))
