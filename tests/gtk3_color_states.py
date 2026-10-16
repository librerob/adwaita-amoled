"""Native GTK3 color regressions for compound and inherited style states."""

import argparse
import collections
import json
from pathlib import Path
import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio

parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
Gtk.init([])
Gio.resources_register(Gio.Resource.load(str(args.root / "gtk-3.0/gtk.gresource")))
provider = Gtk.CssProvider()
errors = []
provider.connect("parsing-error", lambda _p, _s, error: errors.append(str(error)))
provider.load_from_path(str(args.root / "gtk-3.0/gtk.css"))
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
)
F = Gtk.StateFlags


def node(name, classes=(), flags=F.NORMAL):
    return name, classes, flags


def luminance(color):
    return sum(
        (v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
        * weight
        for v, weight in zip(color, (0.2126, 0.7152, 0.0722))
    )


def contrast(foreground, background):
    a, b = luminance(foreground), luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def painted(foreground, alpha, background):
    return [round(v * alpha + b * (1 - alpha)) for v, b in zip(foreground, background)]


def rgb(color):
    return [round(v * 255) for v in (color.red, color.green, color.blue)]


def sample(nodes, base=0, outline=False):
    path = Gtk.WidgetPath.new()
    parent = None
    contexts = []
    opacity = 1
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 64, 48)
    cr = cairo.Context(surface)
    cr.set_source_rgb(base / 255, base / 255, base / 255)
    cr.paint()
    for index, (name, classes, flags) in enumerate(
        [node("window", ("background",)), *nodes]
    ):
        path.append_type(Gtk.Widget)
        path.iter_set_object_name(-1, name)
        path.iter_set_state(-1, flags)
        for cls in classes:
            path.iter_add_class(-1, cls)
        context = Gtk.StyleContext.new()
        context.set_path(path)
        context.set_state(flags)
        if parent:
            context.set_parent(parent)
        # The initial window supplies the foreground; base represents the real
        # dark surface on which the control is placed, including raised cards.
        if index:
            Gtk.render_background(context, cr, 0, 0, 64, 48)
        opacity *= context.get_property("opacity", flags)
        contexts.append(context)
        parent = context
    foreground = (
        parent.get_property("outline-color", flags)
        if outline
        else parent.get_color(flags)
    )
    if outline:
        assert parent.get_property("outline-width", flags) > 0
        assert int(parent.get_property("outline-style", flags)) != 0
    surface.flush()
    data = bytes(surface.get_data())
    colors = collections.Counter(
        tuple(data[y * surface.get_stride() + x * 4 + channel] for channel in (2, 1, 0))
        for y in range(8, 40)
        for x in range(12, 52)
    )
    alpha = foreground.alpha * opacity
    ratios = [
        contrast(
            [
                round(v * alpha + b * (1 - alpha))
                for v, b in zip(rgb(foreground), background)
            ],
            background,
        )
        for background in colors
    ]
    return {
        "foreground": rgb(foreground),
        "alpha": alpha,
        "backgrounds": list(colors),
        "minimum_contrast": min(ratios),
    }


results = []


def check(name, nodes, minimum=4.5, base=0, outline=False):
    row = sample(nodes, base, outline)
    row.update(name=name, minimum_required=minimum, surface=base, outline=outline)
    results.append(row)


for state_name, flags in [
    ("normal", F.NORMAL),
    ("hover", F.PRELIGHT),
    ("backdrop", F.BACKDROP),
    ("hover-backdrop", F.PRELIGHT | F.BACKDROP),
]:
    selected = F.SELECTED | flags
    for classes in [
        (),
        ("dim-label",),
        ("accent",),
        ("error",),
        ("warning",),
        ("success",),
        ("link",),
    ]:
        check(
            "selected-row/" + ".".join(classes) + "/" + state_name,
            [node("row", ("activatable",), selected), node("label", classes)],
        )
    check(
        "selected-row/scale-value/" + state_name,
        [node("row", ("activatable",), selected), node("scale"), node("value")],
    )
    check(
        "menu/accelerator/" + state_name,
        [node("menu"), node("menuitem", flags=flags), node("accelerator")],
    )
    check(
        "header/subtitle/" + state_name,
        [node("headerbar", ("selection-mode",), flags), node("label", ("subtitle",))],
    )
    check(
        "header/selection-arrow/" + state_name,
        [
            node("headerbar", ("selection-mode",), flags),
            node("button", ("selection-menu",), flags),
            node("image", ("arrow",), flags),
        ],
        3,
    )
    check(
        "notebook/close/" + state_name,
        [
            node("notebook"),
            node("header"),
            node("tabs"),
            node("tab", flags=F.CHECKED | flags),
            node("button", ("flat",), flags),
            node("image"),
        ],
        3,
    )
    check(
        "selected-row/flat-button/" + state_name,
        [node("row", ("activatable",), selected), node("button", ("flat",), flags)],
    )
    check(
        "selected-row/flat-button-focus/" + state_name,
        [
            node("row", ("activatable",), selected),
            node("button", ("flat",), flags | F.FOCUSED),
        ],
        3,
        outline=True,
    )


for control in ["check", "radio"]:
    for mark in [F.CHECKED, F.INCONSISTENT, F.CHECKED | F.INCONSISTENT]:
        for modifiers in [
            F.NORMAL,
            F.PRELIGHT,
            F.ACTIVE,
            F.FOCUSED,
            F.BACKDROP,
            F.PRELIGHT | F.FOCUSED,
            F.PRELIGHT | F.BACKDROP,
            F.ACTIVE | F.FOCUSED | F.PRELIGHT,
        ]:
            for base in [0, 20, 26]:
                check(
                    f"{control}/{int(mark)}/{int(modifiers)}",
                    [node("checkbutton"), node(control, flags=mark | modifiers)],
                    3,
                    base,
                )

for flags in [F.NORMAL, F.BACKDROP, F.FOCUSED]:
    check(
        "calendar/adjacent-month/" + str(int(flags)),
        [node("calendar", flags=F.INCONSISTENT | flags)],
    )
    check(
        "content-view/checked/" + str(int(flags)),
        [node("widget", ("content-view",)), node("check", flags=F.CHECKED | flags)],
        3,
    )

check(
    "places-sidebar/drop-selection",
    [node("placessidebar"), node("row", flags=F.DROP_ACTIVE | F.SELECTED)],
)
for name, flags in [
    ("scale", F.FOCUSED),
    ("switch", F.FOCUSED),
    ("switch", F.CHECKED | F.FOCUSED),
    ("row", F.SELECTED | F.FOCUSED),
]:
    check(
        "focus/" + name + "/" + str(int(flags)),
        [node(name, flags=flags)],
        3,
        outline=True,
    )

# GTK's native print renderer uses the same ink for page numbers and rulers.
# These assertions deliberately cover both surfaces, including small 16-up numbers.
for flags in [F.NORMAL, F.BACKDROP]:
    paper = sample([node("printdialog"), node("paper", flags=flags)])
    for background in [[0, 0, 0], [255, 255, 255]]:
        results.append(
            dict(
                paper,
                name="print/ink/" + str(int(flags)) + "/" + str(background[0]),
                minimum_contrast=contrast(
                    painted(paper["foreground"], paper["alpha"], background), background
                ),
                minimum_required=4.5,
            )
        )
    canvas = sample([node("printdialog"), node("notebook"), node("stack", flags=flags)])
    results.append(
        dict(
            paper,
            name="print/rulers/" + str(int(flags)),
            minimum_contrast=min(
                contrast(
                    painted(paper["foreground"], paper["alpha"], background), background
                )
                for background in canvas["backgrounds"]
            ),
            minimum_required=4.5,
        )
    )

context = Gtk.StyleContext.new()
path = Gtk.WidgetPath.new()
path.append_type(Gtk.Window)
path.iter_set_object_name(-1, "window")
path.iter_add_class(-1, "background")
context.set_path(path)
for name in ["accent", "warning_color", "error_color", "success_color"]:
    found, color = context.lookup_color(name)
    assert found, name
    for background in [
        (0, 0, 0),
        (15, 15, 15),
        (20, 20, 20),
        (26, 26, 26),
        (37, 37, 37),
        (17, 24, 32),
    ]:
        results.append(
            {
                "name": "named-standalone/" + name,
                "foreground": rgb(color),
                "background": background,
                "minimum_contrast": contrast(
                    painted(rgb(color), color.alpha, background), background
                ),
                "minimum_required": 7 if name == "accent" else 4.5,
            }
        )

args.output.mkdir(parents=True, exist_ok=True)
(args.output / "gtk3-context-colors.json").write_text(
    json.dumps(results, indent=2) + "\n"
)
assert not errors, errors
failures = [row for row in results if row["minimum_contrast"] < row["minimum_required"]]
print(
    json.dumps(
        {
            "native_gtk3_context_pairs": len(results),
            "failures": len(failures),
            "minimum_contrast": min(row["minimum_contrast"] for row in results),
        }
    )
)
assert not failures, json.dumps(
    [
        {key: row[key] for key in ("name", "minimum_contrast", "minimum_required")}
        for row in failures
    ]
)
