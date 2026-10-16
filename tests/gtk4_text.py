"""Read text colors and group opacity from native GTK4 snapshot nodes.

Use the stable C API for GskRenderNode because older PyGObject releases cannot
translate the concrete render-node subclasses returned by Gtk.Snapshot.
"""

import ctypes as c
from gi.repository import Gtk, Gsk


class RGBA(c.Structure):
    _fields_ = [(channel, c.c_float) for channel in ("red", "green", "blue", "alpha")]


library = c.CDLL("libgtk-4.so.1")


def bind(name, result, arguments):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = arguments
    return function


capsule_pointer = c.pythonapi.PyCapsule_GetPointer
capsule_pointer.restype = c.c_void_p
capsule_pointer.argtypes = [c.py_object, c.c_char_p]


def pointer(obj):
    return capsule_pointer(obj.__gpointer__, None)


def colors(widget):
    paintable = Gtk.WidgetPaintable.new(widget)
    snapshot = Gtk.Snapshot.new()
    bind(
        "gdk_paintable_snapshot", None, [c.c_void_p, c.c_void_p, c.c_double, c.c_double]
    )(pointer(paintable), pointer(snapshot), widget.get_width(), widget.get_height())
    root = bind("gtk_snapshot_to_node", c.c_void_p, [c.c_void_p])(pointer(snapshot))
    assert root, "Widget snapshot was empty"
    node_type = bind("gsk_render_node_get_node_type", c.c_int, [c.c_void_p])
    text_color = bind("gsk_text_node_get_color", c.POINTER(RGBA), [c.c_void_p])
    child_functions = {
        "transform-node": "gsk_transform_node_get_child",
        "clip-node": "gsk_clip_node_get_child",
        "rounded-clip-node": "gsk_rounded_clip_node_get_child",
        "shadow-node": "gsk_shadow_node_get_child",
        "blur-node": "gsk_blur_node_get_child",
        "debug-node": "gsk_debug_node_get_child",
    }
    leaves = {
        "color-node",
        "texture-node",
        "texture-scale-node",
        "cairo-node",
        "border-node",
        "inset-shadow-node",
        "outset-shadow-node",
        "linear-gradient-node",
        "repeating-linear-gradient-node",
        "radial-gradient-node",
        "repeating-radial-gradient-node",
        "conic-gradient-node",
    }
    result = []

    def walk(node, opacity):
        kind = Gsk.RenderNodeType(node_type(node)).value_nick
        if kind == "text-node":
            color = text_color(node).contents
            result.append(
                (
                    [
                        round(getattr(color, channel) * 255)
                        for channel in ("red", "green", "blue")
                    ],
                    color.alpha * opacity,
                )
            )
        elif kind == "container-node":
            count = bind("gsk_container_node_get_n_children", c.c_uint, [c.c_void_p])(
                node
            )
            child = bind(
                "gsk_container_node_get_child", c.c_void_p, [c.c_void_p, c.c_uint]
            )
            for index in range(count):
                walk(child(node, index), opacity)
        elif kind == "opacity-node":
            alpha = bind("gsk_opacity_node_get_opacity", c.c_float, [c.c_void_p])(node)
            child = bind("gsk_opacity_node_get_child", c.c_void_p, [c.c_void_p])(node)
            walk(child, opacity * alpha)
        elif kind in child_functions:
            walk(bind(child_functions[kind], c.c_void_p, [c.c_void_p])(node), opacity)
        else:
            assert (
                kind in leaves
            ), f"Unhandled native node {kind}; update the contrast fixture"

    try:
        walk(root, 1.0)
    finally:
        bind("gsk_render_node_unref", None, [c.c_void_p])(root)
    assert result, "No native text nodes were examined"
    return result
