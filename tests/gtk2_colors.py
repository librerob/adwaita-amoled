import collections, ctypes as c, json, sys, time
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
g = c.CDLL("libgtk-x11-2.0.so.0")
gdk = c.CDLL("libgdk-x11-2.0.so.0")
pix = c.CDLL("libgdk_pixbuf-2.0.so.0")
obj = c.CDLL("libgobject-2.0.so.0")
P = c.c_void_p
I = c.c_int
S = c.c_char_p


class Color(c.Structure):
    _fields_ = [
        ("pixel", c.c_uint32),
        ("red", c.c_uint16),
        ("green", c.c_uint16),
        ("blue", c.c_uint16),
    ]


class Object(c.Structure):
    _fields_ = [("gtype", P), ("refcount", c.c_uint), ("qdata", P)]


class Style(c.Structure):
    _fields_ = [("parent", Object)] + [
        (name, Color * 5)
        for name in ["fg", "bg", "light", "dark", "mid", "text", "base", "text_aa"]
    ]


def fn(lib, name, result, args):
    f = getattr(lib, name)
    f.restype = result
    f.argtypes = args
    return f


fn(g, "gtk_init", None, [P, P])(None, None)
fn(g, "gtk_rc_parse", None, [S])(str(root / "gtk-2.0/gtkrc").encode())
w = fn(g, "gtk_window_new", P, [I])(0)
box = fn(g, "gtk_vbox_new", P, [I, I])(0, 8)
fn(g, "gtk_container_add", None, [P, P])(w, box)
pack = fn(g, "gtk_box_pack_start", None, [P, P, I, I, I])
widgets = []
for name, constructor in [
    ("button", "gtk_button_new_with_label"),
    ("check", "gtk_check_button_new_with_label"),
    ("label", "gtk_label_new"),
]:
    widget = fn(g, constructor, P, [S])((name + " readable text").encode())
    pack(box, widget, 0, 0, 0)
    widgets.append((name, widget, False))
entry = fn(g, "gtk_entry_new", P, [])()
fn(g, "gtk_entry_set_text", None, [P, S])(entry, b"Readable entry")
pack(box, entry, 0, 0, 0)
widgets.append(("entry", entry, True))
scroll = fn(g, "gtk_hscrollbar_new", P, [P])(None)
pack(box, scroll, 0, 0, 0)
widgets.append(("scrollbar", scroll, False))
scale = fn(g, "gtk_hscale_new_with_range", P, [c.c_double, c.c_double, c.c_double])(
    0, 100, 1
)
pack(box, scale, 0, 0, 0)
widgets.append(("scale", scale, False))
fn(g, "gtk_widget_show_all", None, [P])(w)
for _ in range(100):
    while fn(g, "gtk_events_pending", I, [])():
        fn(g, "gtk_main_iteration", I, [])()
    time.sleep(0.002)
stylefn = fn(g, "gtk_widget_get_style", c.POINTER(Style), [P])
rows = []


def rgb(col):
    return [round(x / 257) for x in [col.red, col.green, col.blue]]


def lum(ch):
    return sum(
        (x / 255 / 12.92 if x / 255 <= 0.04045 else ((x / 255 + 0.055) / 1.055) ** 2.4)
        * weight
        for x, weight in zip(ch, [0.2126, 0.7152, 0.0722])
    )


def contrast(a, b):
    return (max(lum(a), lum(b)) + 0.05) / (min(lum(a), lum(b)) + 0.05)


for name, widget, text in widgets:
    style = stylefn(widget)
    assert rgb(style.contents.fg[0]) == [255, 255, 255], (
        name,
        rgb(style.contents.fg[0]),
    )
    for state in range(5):
        fg = rgb((style.contents.text if text else style.contents.fg)[state])
        bg = rgb((style.contents.base if text else style.contents.bg)[state])
        row = {
            "widget": name,
            "state": state,
            "foreground": fg,
            "background": bg,
            "contrast": contrast(fg, bg),
        }
        indicator = name in ["scrollbar", "scale"]
        row["minimum_required"] = 3 if indicator else 4.5
        if indicator:
            row["contrast"] = contrast(bg, [0, 0, 0])
        if (name == "button" or indicator) and state != 4:
            drawable = fn(gdk, "gdk_pixmap_new", P, [P, I, I, I])(
                fn(g, "gtk_widget_get_window", P, [P])(widget), 240, 48, -1
            )
            if indicator:
                fn(g, "gtk_paint_slider", None, [P, P, I, I, P, P, S, I, I, I, I, I])(
                    style,
                    drawable,
                    state,
                    2,
                    None,
                    widget,
                    b"hscrollbar" if name == "scrollbar" else b"hscale",
                    0,
                    0,
                    240,
                    48,
                    0,
                )
            else:
                fn(g, "gtk_paint_box", None, [P, P, I, I, P, P, S, I, I, I, I])(
                    style, drawable, state, 2, None, widget, b"button", 0, 0, 240, 48
                )
            image = fn(
                gdk, "gdk_pixbuf_get_from_drawable", P, [P, P, P, I, I, I, I, I, I]
            )(
                None,
                drawable,
                fn(gdk, "gdk_colormap_get_system", P, [])(),
                0,
                0,
                0,
                0,
                240,
                48,
            )
            stride = fn(pix, "gdk_pixbuf_get_rowstride", I, [P])(image)
            channels = fn(pix, "gdk_pixbuf_get_n_channels", I, [P])(image)
            data = c.string_at(
                fn(pix, "gdk_pixbuf_get_pixels", P, [P])(image), stride * 48
            )
            backgrounds = {
                tuple(data[y * stride + x * channels : y * stride + x * channels + 3])
                for y in range(8, 40)
                for x in range(20, 220)
            }
            if indicator:
                row["minimum_painted_indicator_contrast"] = min(
                    contrast(b, [0, 0, 0]) for b in backgrounds
                )
            else:
                row["minimum_painted_button_contrast"] = min(
                    contrast(fg, b) for b in backgrounds
                )
            fn(obj, "g_object_unref", None, [P])(image)
            fn(obj, "g_object_unref", None, [P])(drawable)
        rows.append(row)
(out / "colors.json").write_text(json.dumps(rows, indent=2) + "\n")
print(
    json.dumps(
        {
            "gtk2_style_pairs": len(rows),
            "painted_button_states": sum(
                "minimum_painted_button_contrast" in r for r in rows
            ),
            "painted_indicator_states": sum(
                "minimum_painted_indicator_contrast" in r for r in rows
            ),
            "minimum_painted_indicator_contrast": min(
                r["minimum_painted_indicator_contrast"]
                for r in rows
                if "minimum_painted_indicator_contrast" in r
            ),
            "minimum_painted_contrast": min(
                r["minimum_painted_button_contrast"]
                for r in rows
                if "minimum_painted_button_contrast" in r
            ),
        }
    )
)
fn(g, "gtk_widget_destroy", None, [P])(w)
assert all(
    r["contrast"] >= r["minimum_required"] for r in rows if r["state"] != 4
), rows
assert all(
    r["minimum_painted_indicator_contrast"] >= 3
    for r in rows
    if "minimum_painted_indicator_contrast" in r
), rows
assert all(
    r["minimum_painted_button_contrast"] >= 4.5
    for r in rows
    if "minimum_painted_button_contrast" in r
)
