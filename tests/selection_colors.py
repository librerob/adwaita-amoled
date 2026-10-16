"""Measure native ordinary, secondary and semantic text inside selected rows."""

import gi, cairo, json, sys, time, collections
from pathlib import Path

root = Path(sys.argv[1])
version = sys.argv[2]
adw = "--adw" in sys.argv
light = "--light" in sys.argv
out = Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
gi.require_version("Gtk", version)
from gi.repository import Gtk, Gdk, Gio, GLib

if version == "3.0":
    Gtk.init([])
else:
    Gtk.init()
Gtk.Settings.get_default().set_property("gtk-enable-animations", False)
Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", not light)
if adw:
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    Adw.init()
    Adw.StyleManager.get_default().set_color_scheme(
        Adw.ColorScheme.FORCE_LIGHT if light else Adw.ColorScheme.FORCE_DARK
    )
for v in ["3.0", "4.0"]:
    Gio.resources_register(Gio.Resource.load(str(root / f"gtk-{v}/gtk.gresource")))
p = Gtk.CssProvider()
p.load_from_path(
    str(
        root
        / (
            (
                "extra/libadwaita/gtk-modern.css"
                if Gtk.get_minor_version() >= 16
                else "extra/libadwaita/gtk.css"
            )
            if adw
            else f"gtk-{version}/gtk.css"
        )
    )
)
if version == "3.0":
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), p, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
else:
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), p, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
    sys.path.insert(0, str(root / "tests"))
    from gtk4_text import colors as textcolors


def lum(ch):
    return sum(
        (v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
        * w
        for v, w in zip(ch, [0.2126, 0.7152, 0.0722])
    )


def ratio(f, b):
    return (max(lum(f), lum(b)) + 0.05) / (min(lum(f), lum(b)) + 0.05)


def pump():
    end = time.monotonic() + 0.12
    while time.monotonic() < end:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(0.002)


rows = []
for role in [
    "plain",
    "dim-label",
    "accent",
    "error",
    "warning",
    "success",
    "link",
    "button-link",
    "button-visited",
    "button-suggested",
    "button-destructive",
]:
    for state, flags in [
        ("selected", Gtk.StateFlags.SELECTED),
        ("selected-hover", Gtk.StateFlags.SELECTED | Gtk.StateFlags.PRELIGHT),
        ("selected-backdrop", Gtk.StateFlags.SELECTED | Gtk.StateFlags.BACKDROP),
    ]:
        w = Gtk.Window()
        w.set_default_size(480, 80)
        l = Gtk.ListBox()
        r = Gtk.ListBoxRow()
        if role in ["button-link", "button-visited"]:
            label = Gtk.LinkButton.new_with_label(
                "https://example.org", "Selected link"
            )
            label.set_visited(role == "button-visited")
        elif role.startswith("button-"):
            label = Gtk.Button(label="Selected flat action")
            label.get_style_context().add_class("flat")
            label.get_style_context().add_class(
                "suggested-action"
                if role == "button-suggested"
                else "destructive-action"
            )
        else:
            label = Gtk.Label(label="Readable selected row text")
            if role != "plain":
                label.get_style_context().add_class(role)
        if version == "3.0":
            r.add(label)
            l.add(r)
            w.add(l)
            w.show_all()
        else:
            r.set_child(label)
            l.append(r)
            w.set_child(l)
            w.present()
        l.select_row(r)
        r.set_state_flags(flags, True)
        pump()
        if version == "3.0":
            text_widget = label.get_child() if isinstance(label, Gtk.Button) else label
            c = text_widget.get_style_context()
            fg = c.get_color(text_widget.get_state_flags())
            colors = [([round(v * 255) for v in [fg.red, fg.green, fg.blue]], fg.alpha)]
            parent = text_widget
            opacity = 1
            while parent:
                opacity *= (
                    parent.get_style_context().get_property(
                        "opacity", parent.get_state_flags()
                    )
                    * parent.get_opacity()
                )
                parent = parent.get_parent()
            colors = [(f, a * opacity) for f, a in colors]
        else:
            colors = textcolors(label)
        chain = []
        parent = label
        while parent:
            chain.append(parent)
            parent = parent.get_parent()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 240, 48)
        cr = cairo.Context(surface)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        for parent in reversed(chain):
            Gtk.render_background(parent.get_style_context(), cr, 0, 0, 240, 48)
        surface.flush()
        data = bytes(surface.get_data())
        background = list(
            reversed(
                data[
                    24 * surface.get_stride()
                    + 120 * 4 : 24 * surface.get_stride()
                    + 120 * 4
                    + 3
                ]
            )
        )
        ratios = [
            ratio(
                [round(v * a + b * (1 - a)) for v, b in zip(f, background)], background
            )
            for f, a in colors
        ]
        rows.append(
            {
                "role": role,
                "state": state,
                "text_colors": colors,
                "background": background,
                "contrast": min(ratios),
            }
        )
        w.destroy()
        pump()
(out / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
print(
    json.dumps(
        {
            "native_selected_row_pairs": len(rows),
            "minimum_contrast": min(r["contrast"] for r in rows),
        }
    )
)
assert all(r["contrast"] >= 4.5 for r in rows), json.dumps(rows)
