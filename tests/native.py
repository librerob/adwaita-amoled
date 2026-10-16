"""Native consumer checks, each GTK version isolated in its own process."""
import ctypes as c
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ['THEME_TEST_OUTPUT']) if os.environ.get('THEME_TEST_OUTPUT') else None


def metacity():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    Gtk.init([])

    class Error(c.Structure):
        _fields_ = [('domain', c.c_uint), ('code', c.c_int), ('message', c.c_char_p)]

    class Rectangle(c.Structure):
        _fields_ = [('x', c.c_int), ('y', c.c_int), ('width', c.c_int), ('height', c.c_int)]

    class Border(c.Structure):
        _fields_ = [(name, c.c_short) for name in ('left', 'right', 'top', 'bottom')]

    class Borders(c.Structure):
        _fields_ = [(name, Border) for name in ('visible', 'shadow', 'resize', 'invisible', 'total')]

    lib = c.CDLL('libmetacity.so.3')
    cairo = c.CDLL('libcairo.so.2')

    def bind(library, name, result, args):
        function = getattr(library, name)
        function.restype, function.argtypes = result, args
        return function

    new = bind(lib, 'meta_theme_new', c.c_void_p, [c.c_int])
    load = bind(lib, 'meta_theme_load', c.c_int,
                [c.c_void_p, c.c_char_p, c.POINTER(c.POINTER(Error))])
    theme = new(1)
    error = c.POINTER(Error)()
    if not load(theme, b'Adwaita-AMOLED', c.byref(error)):
        raise AssertionError(error.contents.message.decode())
    set_scale = bind(lib, 'meta_theme_set_scale', None, [c.c_void_p, c.c_int])
    bind(lib, 'meta_theme_set_composited', None, [c.c_void_p, c.c_int])(theme, 1)
    bind(lib, 'meta_theme_set_dpi', None, [c.c_void_p, c.c_double])(theme, 96.0)
    # Exercise all four button types exposed by modern libmetacity.
    bind(lib, 'meta_theme_set_button_layout', None, [c.c_void_p, c.c_char_p, c.c_int])(
        theme, b'menu:minimize,maximize,close', 0)
    pango = c.CDLL('libpango-1.0.so.0')
    font = bind(pango, 'pango_font_description_from_string', c.c_void_p, [c.c_char_p])(b'Sans 10')
    bind(lib, 'meta_theme_set_titlebar_font', None, [c.c_void_p, c.c_void_p])(theme, font)
    bind(pango, 'pango_font_description_free', None, [c.c_void_p])(font)
    get_borders = bind(lib, 'meta_theme_get_frame_borders', None,
                       [c.c_void_p, c.c_char_p, c.c_int, c.c_int, c.POINTER(Borders)])
    callback_type = c.CFUNCTYPE(c.c_int, c.c_int, Rectangle, c.c_void_p)
    draw = bind(lib, 'meta_theme_draw_frame', None, [
        c.c_void_p, c.c_char_p, c.c_void_p, c.c_int, c.c_int, c.c_int, c.c_int,
        c.c_char_p, callback_type, c.c_void_p, c.c_void_p, c.c_void_p])
    surface_new = bind(cairo, 'cairo_image_surface_create', c.c_void_p, [c.c_int, c.c_int, c.c_int])
    context_new = bind(cairo, 'cairo_create', c.c_void_p, [c.c_void_p])
    context_status = bind(cairo, 'cairo_status', c.c_int, [c.c_void_p])
    destroy = bind(cairo, 'cairo_destroy', None, [c.c_void_p])
    surface_destroy = bind(cairo, 'cairo_surface_destroy', None, [c.c_void_p])
    write = bind(cairo, 'cairo_surface_write_to_png', c.c_int, [c.c_void_p, c.c_char_p])
    states = {'normal': 0, 'shaded': 1 << 7, 'maximized': 1 << 9,
              'maximized-shaded': (1 << 7) | (1 << 9), 'tiled-left': 1 << 15, 'tiled-right': 1 << 16}
    frames = 0
    for scale in (1, 2):
        set_scale(theme, scale)
        for frame_type in range(7):
            for focus in (False, True):
                for name, state in states.items():
                    flags = ((1 << 6) - 1) | (1 << 10) | (1 << 11) | state
                    if focus:
                        flags |= 1 << 6
                    borders = Borders()
                    get_borders(theme, None, frame_type, flags, c.byref(borders))
                    if frame_type in (4, 5):
                        assert borders.visible.top == 0, (frame_type, name, borders.visible.top)
                    else:
                        assert borders.visible.top > 0, (frame_type, name)
                    for button_state in range(3):
                        callback = callback_type(lambda *_: button_state)
                        surface = surface_new(0, 640 * scale, 300 * scale)
                        context = context_new(surface)
                        draw(theme, None, context, frame_type, flags, 600, 200,
                             b'Adwaita-AMOLED audit', callback, None, None, None)
                        assert context_status(context) == 0
                        if OUTPUT and name == 'normal' and focus and button_state == 0:
                            path = OUTPUT / f'metacity-type{frame_type}-scale{scale}.png'
                            assert write(surface, os.fsencode(path)) == 0
                        destroy(context)
                        surface_destroy(surface)
                        frames += 1
    bind(c.CDLL('libgobject-2.0.so.0'), 'g_object_unref', None, [c.c_void_p])(theme)
    print(json.dumps({'metacity_frames': frames, 'scales': [1, 2], 'window_types': 7}))


def capture():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
    Gtk.init([])
    root = Gdk.get_default_root_window()
    Gdk.pixbuf_get_from_window(root, 0, 0, root.get_width(), root.get_height()).savev(
        sys.argv[2], 'png', [], [])


def gtk(version, adwaita=False):
    import gi
    gi.require_version('Gtk', version)
    from gi.repository import Gtk, Gdk, Gio, GLib
    if version == '3.0':
        Gtk.init([])
    else:
        Gtk.init()
    if adwaita:
        gi.require_version('Adw', '1')
        from gi.repository import Adw
        Adw.init()
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    else:
        settings = Gtk.Settings.get_default()
        settings.set_property('gtk-theme-name', 'Adwaita-AMOLED')
        settings.set_property('gtk-application-prefer-dark-theme', True)

    registered = []
    for v in ('3.0', '4.0'):
        resource = Gio.Resource.load(str(ROOT / f'gtk-{v}/gtk.gresource'))
        Gio.resources_register(resource)
        registered.append(resource)
    paths = [ROOT / f'gtk-{version}/gtk.css', ROOT / f'gtk-{version}/gtk-dark.css']
    if version == '4.0':
        paths.extend(ROOT / name for name in ('src/gtk-4.0/gtk-main.css', 'extra/libadwaita/gtk.css'))
    errors = []
    providers = []
    for path in paths:
        provider = Gtk.CssProvider()
        provider.connect('parsing-error', lambda _p, _s, error: errors.append(str(error)))
        provider.load_from_path(str(path))
        providers.append(provider)
    assert not errors, errors
    if adwaita:
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), providers[-1],
                                                  Gtk.STYLE_PROVIDER_PRIORITY_USER)
    window = Gtk.Window(title='Adwaita-AMOLED regression')
    window.set_default_size(600, 500)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    if version == '3.0':
        window.add(box)
        def add(child):
            box.pack_start(child, False, False, 0)
    else:
        window.set_child(box)
        def add(child):
            box.append(child)
    button = Gtk.Button(label='Suggested action')
    button.get_style_context().add_class('suggested-action')
    add(button)
    success = None
    if adwaita:
        success = Gtk.Button(label='Successful operation')
        success.add_css_class('success')
        success.add_css_class('suggested-action')
        add(success)
    check = Gtk.CheckButton(label='Checked')
    check.set_active(True)
    add(check)
    mixed = Gtk.CheckButton(label='Indeterminate')
    mixed.set_inconsistent(True)
    add(mixed)
    entry = Gtk.Entry()
    entry.set_text('Text and selection')
    add(entry)
    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
    scale.set_value(50)
    add(scale)
    if adwaita:
        rows = Gtk.ListBox()
        rows.append(Adw.ActionRow(title='Libadwaita row', subtitle='AMOLED surfaces'))
        add(rows)
    if version == '3.0':
        window.show_all()
    else:
        window.present()
    context = GLib.MainContext.default()
    def pump(duration=.08):
        end = time.monotonic() + duration
        while time.monotonic() < end:
            while context.pending():
                context.iteration(False)
            time.sleep(.002)
    pump()
    success_contrast = None
    if success is not None:
        from test_theme import contrast
        style = success.get_style_context()
        found_fg, foreground = style.lookup_color('success_fg_color')
        found_bg, background = style.lookup_color('success_bg_color')
        assert found_fg and found_bg
        def hex_color(color):
            return '#' + ''.join(f'{round(channel * 255):02x}'
                                 for channel in (color.red, color.green, color.blue))
        success_contrast = contrast(hex_color(foreground), hex_color(background))
        assert success_contrast >= 4.5, f'Success text contrast is {success_contrast}:1'
        if (Adw.get_major_version(), Adw.get_minor_version()) >= (1, 7):
            # Libadwaita 1.7 maps .success onto the accent variables consumed by
            # .suggested-action. Check the widget's resolved foreground as well.
            assert hex_color(style.get_color()) == hex_color(foreground)
    state_mask = Gtk.StateFlags.CHECKED | Gtk.StateFlags.INCONSISTENT
    original = {w: w.get_state_flags() & state_mask for w in (button, check, mixed, entry)}
    for name, flag in [('normal', Gtk.StateFlags.NORMAL), ('hover', Gtk.StateFlags.PRELIGHT),
                       ('disabled', Gtk.StateFlags.INSENSITIVE), ('backdrop', Gtk.StateFlags.BACKDROP),
                       ('focus', Gtk.StateFlags.FOCUSED), ('active', Gtk.StateFlags.ACTIVE)]:
        for widget, base in original.items():
            widget.set_state_flags(base | flag, True)
        pump()
        if OUTPUT:
            suffix = 'adw' if adwaita else version
            subprocess.run([sys.executable, __file__, '--capture',
                            str(OUTPUT / f'gtk-{suffix}-{name}.png')], check=True, timeout=20)
    for widget, base in original.items():
        widget.set_state_flags(base, True)
    signals = {'toggled': 0, 'clicked': 0}
    def increment(name):
        def callback(_):
            signals[name] += 1
        return callback
    check.connect('toggled', increment('toggled'))
    button.connect('clicked', increment('clicked'))
    for i in range(2000):
        check.set_active(not check.get_active())
        button.emit('clicked')
        if i % 20 == 0:
            while context.pending():
                context.iteration(False)
    assert signals == {'toggled': 2000, 'clicked': 2000}
    for _ in range(200):
        stress = Gtk.Window()
        if version == '3.0':
            stress.add(Gtk.Button(label='Stress'))
            stress.show_all()
        else:
            stress.set_child(Gtk.Button(label='Stress'))
            stress.present()
        while context.pending():
            context.iteration(False)
        stress.destroy()
    if version == '3.0':
        # The original almost-black handle fails this pixel-level regression.
        offscreen = Gtk.OffscreenWindow()
        offscreen.set_default_size(320, 80)
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        slider.set_draw_value(False)
        slider.set_value(50)
        offscreen.add(slider)
        offscreen.show_all()
        pump()
        image = offscreen.get_pixbuf()
        offset = (image.get_height() // 2) * image.get_rowstride() + (image.get_width() // 2) * image.get_n_channels()
        rgb = tuple(image.get_pixels()[offset:offset + 3])
        assert min(rgb) >= 0x70, f'Slider handle is too dark: {rgb}'
        offscreen.destroy()
    window.destroy()
    assert not errors, errors
    print(json.dumps({'gtk': version, 'libadwaita': adwaita, 'parser_errors': errors,
                      'success_text_contrast': success_contrast,
                      'window_lifecycles': 200, 'signals': signals}))


if __name__ == '__main__':
    if OUTPUT:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == '--metacity':
        metacity()
    elif sys.argv[1] == '--capture':
        capture()
    else:
        gtk(sys.argv[1], '--adw' in sys.argv)
