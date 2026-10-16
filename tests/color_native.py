import argparse, collections, json, os, sys, time
from pathlib import Path
import cairo, gi

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
p.add_argument("consumer", choices=["gtk3", "gtk4", "adw"])
p.add_argument("output", type=Path)
p.add_argument("--light", action="store_true")
a = p.parse_args()
version = "3.0" if a.consumer == "gtk3" else "4.0"
gi.require_version("Gtk", version)
from gi.repository import Gtk, Gdk, Gio, GLib

if version == "3.0":
    Gtk.init([])
else:
    Gtk.init()
Gtk.Settings.get_default().set_property("gtk-enable-animations", False)
Gtk.Settings.get_default().set_property(
    "gtk-application-prefer-dark-theme", not a.light
)
if a.consumer == "adw":
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    Adw.init()
    Adw.StyleManager.get_default().set_color_scheme(
        Adw.ColorScheme.FORCE_LIGHT if a.light else Adw.ColorScheme.FORCE_DARK
    )
if version == "4.0":
    from gtk4_text import colors as native_text_colors

for v in ["3.0", "4.0"]:
    r = Gio.Resource.load(str(a.root / f"gtk-{v}/gtk.gresource"))
    Gio.resources_register(r)
provider = Gtk.CssProvider()
errors = []
provider.connect("parsing-error", lambda _p, _s, e: errors.append(str(e)))
if a.consumer == "adw":
    path = (
        a.root
        / "extra/libadwaita"
        / ("gtk-modern.css" if Gtk.get_minor_version() >= 16 else "gtk.css")
    )
else:
    path = a.root / f"gtk-{version}/gtk.css"
provider.load_from_path(str(path))
if version == "3.0":
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
else:
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
w = Gtk.Window()
w.set_default_size(560, 1000)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
if version == "3.0":
    w.add(box)
else:
    w.set_child(box)


def add(widget):
    if version == "3.0":
        box.pack_start(widget, False, False, 0)
    else:
        box.append(widget)


def classes(widget, *names):
    for name in names:
        widget.get_style_context().add_class(name)


items = []
for name, cls in [
    ("button", ""),
    ("suggested", "suggested-action"),
    ("destructive", "destructive-action"),
    ("flat-suggested", "flat suggested-action"),
    ("flat-destructive", "flat destructive-action"),
    ("success-filled", "success suggested-action"),
    ("warning-filled", "warning suggested-action"),
    ("error-filled", "error suggested-action"),
]:
    b = Gtk.Button(label=name)
    if cls:
        classes(b, *cls.split())
    add(b)
    items.append((name, b))
if version == "4.0":
    for status in ["success", "warning", "error"]:
        button = Gtk.Button(label="Flat " + status + " action")
        classes(button, status, "suggested-action", "flat")
        add(button)
        items.append(("flat-" + status, button))
for name in ["accent", "error", "warning", "success", "dim-label", "link"]:
    label = Gtk.Label(label=name + " readable text")
    classes(label, name)
    add(label)
    items.append((name, label))
progress = Gtk.ProgressBar()
progress.set_fraction(0.57)
progress.set_show_text(True)
progress.set_text("Readable progress 57%")
add(progress)
items.append(("progress", progress))
e = Gtk.Entry()
e.set_text("Editable text")
add(e)
items.append(("entry", e))
for name in ["error", "warning"]:
    e = Gtk.Entry()
    e.set_text(name + " entry")
    classes(e, name)
    add(e)
    items.append((name + "-entry", e))
if version == "3.0":
    link = Gtk.LinkButton.new_with_label("https://example.org", "A readable link")
    add(link)
    items.append(("link-button", link))
else:
    link = Gtk.LinkButton.new_with_label("https://example.org", "A readable link")
    add(link)
    items.append(("link-button", link))
if version == "3.0":
    for role in ["tasklist", "launcher"]:
        parent = Gtk.Box()
        classes(parent, role)
        panel_button = Gtk.Button(label=role + " panel button")
        parent.add(panel_button)
        add(parent)
        items.append((role, panel_button))
if version == "3.0":
    w.show_all()
else:
    w.present()
ctx = GLib.MainContext.default()


def pump():
    end = time.monotonic() + 0.08
    while time.monotonic() < end:
        while ctx.pending():
            ctx.iteration(False)
        time.sleep(0.002)


def rgb(col):
    return [round(x * 255) for x in [col.red, col.green, col.blue]]


def lum(c):
    v = [x / 255 for x in c]
    return sum(
        (x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) * z
        for x, z in zip(v, [0.2126, 0.7152, 0.0722])
    )


def contrast(f, b):
    return (max(lum(f), lum(b)) + 0.05) / (min(lum(f), lum(b)) + 0.05)


def bgpaint(widget):
    # Composite actual style backgrounds from the window down to this widget.
    chain = []
    c = widget
    while c:
        chain.append(c)
        c = c.get_parent()
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 240, 48)
    cr = cairo.Context(surface)
    cr.set_source_rgb(0, 0, 0)
    cr.paint()
    for c in reversed(chain):
        Gtk.render_background(c.get_style_context(), cr, 0, 0, 240, 48)
    surface.flush()
    data = bytes(surface.get_data())
    stride = surface.get_stride()
    pixels = [
        tuple(data[y * stride + x * 4 + i] for i in [2, 1, 0])
        for y in range(8, 40)
        for x in range(20, 220)
    ]
    # Keep every background gradient sample; contrast against its worst point.
    return surface, collections.Counter(pixels)


results = []
a.output.mkdir(parents=True, exist_ok=True)
pump()
for name, widget in items:
    original = widget.get_state_flags()
    for state, flag in [
        ("normal", Gtk.StateFlags.NORMAL),
        ("hover", Gtk.StateFlags.PRELIGHT),
        ("active", Gtk.StateFlags.ACTIVE),
        ("checked", Gtk.StateFlags.CHECKED),
        ("backdrop", Gtk.StateFlags.BACKDROP),
        ("disabled", Gtk.StateFlags.INSENSITIVE),
        ("focus-hover", Gtk.StateFlags.FOCUSED | Gtk.StateFlags.PRELIGHT),
        ("active-hover", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT),
        ("backdrop-active", Gtk.StateFlags.BACKDROP | Gtk.StateFlags.ACTIVE),
        ("backdrop-hover", Gtk.StateFlags.BACKDROP | Gtk.StateFlags.PRELIGHT),
        (
            "focus",
            Gtk.StateFlags.FOCUSED
            | getattr(Gtk.StateFlags, "FOCUS_VISIBLE", Gtk.StateFlags.NORMAL),
        ),
    ]:
        widget.set_state_flags(original | flag, True)
        pump()
        text_widget = widget.get_child() if isinstance(widget, Gtk.Button) else widget
        style = text_widget.get_style_context()
        fg = (
            style.get_color(text_widget.get_state_flags())
            if version == "3.0"
            else style.get_color()
        )
        text_colors = [(rgb(fg), fg.alpha)]
        if version == "4.0":
            text_colors = native_text_colors(widget)
        else:
            opacity = 1.0
            parent = text_widget
            while parent:
                parent_style = parent.get_style_context()
                opacity *= (
                    parent_style.get_property("opacity", parent.get_state_flags())
                    * parent.get_opacity()
                )
                parent = parent.get_parent()
            text_colors = [(rgb(fg), fg.alpha * opacity)]
        if version == "3.0" and name in ["tasklist", "launcher"] and state == "focus":
            focus_style = widget.get_style_context()
            assert (
                focus_style.get_property("outline-width", widget.get_state_flags()) >= 2
            )
        if name == "dim-label" and state == "normal":
            assert any(
                0 < alpha < 1 for _, alpha in text_colors
            ), "CSS opacity was not measured"
        if (
            name in ["flat-success", "flat-warning", "flat-error"]
            and state != "disabled"
        ):
            found, expected = style.lookup_color(name.removeprefix("flat-") + "_color")
            assert found
            assert all(foreground == rgb(expected) for foreground, _ in text_colors), (
                name,
                state,
                text_colors,
            )
        surface, colors = bgpaint(widget)
        background, count = colors.most_common(1)[0]
        ratios = [
            contrast(
                [
                    round(channel * alpha + value * (1 - alpha))
                    for channel, value in zip(foreground, background)
                ],
                background,
            )
            for foreground, alpha in text_colors
            for background in colors
        ]
        row = {
            "widget": name,
            "state": state,
            "foreground": rgb(fg),
            "foreground_alpha": fg.alpha,
            "native_text_colors": text_colors,
            "dominant_background": background,
            "minimum_contrast": min(ratios),
            "maximum_contrast": max(ratios),
        }
        results.append(row)
        surface.write_to_png(str(a.output / f"{name}-{state}-background.png"))
    widget.set_state_flags(original, True)
# Resolve GTK3's real CSS node names separately from their text-bearing parent.
# Check marks/radio dots use the graphic threshold, not the ordinary-text one.
if version == "3.0":
    graphics = []
    for node_name in ["check", "radio", "calendar-arrow"]:
        path = Gtk.WidgetPath.new()
        if node_name == "calendar-arrow":
            path.append_type(Gtk.Calendar)
            path.iter_set_object_name(-1, "calendar")
            path.iter_add_class(-1, "button")
        else:
            path.append_type(Gtk.CheckButton)
            path.iter_set_object_name(-1, "checkbutton")
            path.append_type(Gtk.CheckButton)
            path.iter_set_object_name(-1, node_name)
        style = Gtk.StyleContext.new()
        style.set_path(path)
        for state, flag in [
            ("normal", Gtk.StateFlags.NORMAL),
            ("hover", Gtk.StateFlags.PRELIGHT),
            ("backdrop", Gtk.StateFlags.BACKDROP),
            ("checked", Gtk.StateFlags.CHECKED),
            ("checked-backdrop", Gtk.StateFlags.CHECKED | Gtk.StateFlags.BACKDROP),
            ("indeterminate", Gtk.StateFlags.INCONSISTENT),
            (
                "indeterminate-backdrop",
                Gtk.StateFlags.INCONSISTENT | Gtk.StateFlags.BACKDROP,
            ),
        ]:
            if node_name == "calendar-arrow" and state not in [
                "normal",
                "hover",
                "backdrop",
            ]:
                continue
            style.set_state(flag)
            marked = node_name == "calendar-arrow" or bool(
                flag & (Gtk.StateFlags.CHECKED | Gtk.StateFlags.INCONSISTENT)
            )
            ink = style.get_color(flag) if marked else style.get_border_color(flag)
            for base in [0, 20, 26]:
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 32, 32)
                cr = cairo.Context(surface)
                cr.set_source_rgb(base / 255, base / 255, base / 255)
                cr.paint()
                Gtk.render_background(style, cr, 0, 0, 32, 32)
                surface.flush()
                data = bytes(surface.get_data())
                offset = 16 * surface.get_stride() + 16 * 4
                background = list(reversed(data[offset : offset + 3]))
                foreground = [
                    round(channel * ink.alpha + value * (1 - ink.alpha))
                    for channel, value in zip(rgb(ink), background)
                ]
                graphics.append(
                    {
                        "node": node_name,
                        "state": state,
                        "surface": base,
                        "foreground": foreground,
                        "background": background,
                        "contrast": contrast(foreground, background),
                    }
                )
    (a.output / "graphics.json").write_text(json.dumps(graphics, indent=2) + "\n")
    print(
        json.dumps(
            {
                "gtk3_graphic_pairs": len(graphics),
                "minimum_graphic_contrast": min(row["contrast"] for row in graphics),
            }
        )
    )
    assert all(row["contrast"] >= 3 for row in graphics), graphics
w.destroy()
assert not errors, errors
(a.output / "colors.json").write_text(json.dumps(results, indent=2) + "\n")
print(
    json.dumps(
        {
            "consumer": a.consumer,
            "light_request": a.light,
            "pairs": len(results),
            "minimum_enabled_text_contrast": min(
                r["minimum_contrast"] for r in results if r["state"] != "disabled"
            ),
        }
    )
)

failures = [
    r for r in results if r["state"] != "disabled" and r["minimum_contrast"] < 4.5
]
assert not failures, json.dumps(failures)
