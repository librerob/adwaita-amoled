"""Resolve GTK2's installed theme by name, without gtk_rc_parse or RC overrides."""

import ctypes as c
import json
import time

gtk = c.CDLL("libgtk-x11-2.0.so.0")
gobject = c.CDLL("libgobject-2.0.so.0")
P, I, S = c.c_void_p, c.c_int, c.c_char_p


def bind(library, name, result, arguments):
    function = getattr(library, name)
    function.restype, function.argtypes = result, arguments
    return function


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
        for name in ("fg", "bg", "light", "dark", "mid", "text", "base", "text_aa")
    ]


bind(gtk, "gtk_init", None, [P, P])(None, None)
settings = bind(gtk, "gtk_settings_get_default", P, [])()
bind(gobject, "g_object_set", None, [P, S, S, P])(
    settings, b"gtk-theme-name", b"Adwaita-AMOLED", None
)
bind(gtk, "gtk_rc_reparse_all_for_settings", I, [P, I])(settings, 1)
window = bind(gtk, "gtk_window_new", P, [I])(0)
bind(gtk, "gtk_widget_show_all", None, [P])(window)
for _ in range(40):
    while bind(gtk, "gtk_events_pending", I, [])():
        bind(gtk, "gtk_main_iteration", I, [])()
    time.sleep(0.002)
style = bind(gtk, "gtk_widget_get_style", c.POINTER(Style), [P])(window).contents


def rgb(color):
    return [round(channel / 257) for channel in (color.red, color.green, color.blue)]


background, foreground = rgb(style.bg[0]), rgb(style.fg[0])
print(
    json.dumps(
        {
            "normal_theme_discovery": background == [0, 0, 0]
            and foreground == [255, 255, 255],
            "background": background,
            "foreground": foreground,
        }
    )
)
bind(gtk, "gtk_widget_destroy", None, [P])(window)
