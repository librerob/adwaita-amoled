# Upstream compatibility review — 16 October 2026

The GTK and libadwaita theme was compared with the current stable upstream
styles and exercised with native consumers. One compatibility defect was
reproduced and addressed: modern libadwaita derives standalone text colors from
the requested light/dark scheme, while the AMOLED override keeps surfaces dark.
The legacy overrides alone could therefore produce dark text on black.

Use the modern entry point described in [the installation instructions](INSTALLING.md#gtk4-entry-point)
on GTK 4.16 or newer. Keep the legacy entry point on older GTK releases.

## Versions and coverage

| Component | Stable target checked | Evidence and boundary |
| --- | --- | --- |
| GNOME | 51; Shell 51.1 | Shell theme derived from the pinned 51.1 default. Native headless Wayland Shell 51.1 loads it through User Themes; surface colors, eight rendered views, 40 menu transitions and 6,822 style-state queries at 1×/2× verified. Isolated service mocks are used; real login and authentication are not tested. Application styling tested through GTK/libadwaita below. |
| GTK3 / Adwaita | 3.24.52 | Native parsing, widget states, slider pixels, window lifecycle and callback checks on X11 and Wayland. |
| GTK4 / Default | 4.24.1 | Native parsing and rendering on X11 and Wayland. The theme's runtime import still resolves GTK's own `Default-dark.css`, retaining the installed toolkit's widget definitions. |
| libadwaita | 1.10.0 | Native light/dark color checks; current sidebars, overlay sidebar, dropdown styles, GTK/Adwaita spinners, toggle group, banner and preference rows rendered. Stock Adwaita used as a control. |
| Cinnamon / Muffin | 6.6.9 / 6.6.3 | Cinnamon X11 session loaded this repository's stylesheet. Menu and decorations rendered; three GTK clients, 180 EWMH state requests and 30 observed state transitions. Existing Cinnamon 6.6 menu selectors remain applicable. |
| Xfce | 4.20; panel 4.20.8, Xfwm4 4.20.0 | Native X11 panel/settings/window-manager integration with three GTK clients and 60 focus switches. The repository provides GTK panel styling, but no Xfwm4 decoration theme. |
| MATE / Marco | 1.28 stable series; Marco 1.28.2 | Marco built from its upstream tag, loaded the decoration theme and rendered three native clients. 180 state requests and 30 observed transitions. This was a window-manager test, not a complete MATE login session. |
| Budgie | 10.10.3 | Built from the checksum-verified official release archive. Panel and Raven ran on headless Wayland/labwc; the D-Bus version was verified and 10 Raven expansion transitions observed. Budgie's built-in shell theme stayed enabled. This repository supplies GTK application styling, not a dedicated Budgie shell theme. |

Newest tags are not always stable desktop releases: Cinnamon also publishes
automated builds, Xfce has a 4.21 development series, and MATE has 1.29
development components. Those were not substituted for the stable targets.

## Folder icon application checks

On 19 October 2026, all eight folder presets were exercised in actual windows
of the following applications, installed using the Bash installer:

| Application | Version | Checked with each preset |
| --- | --- | --- |
| Nemo | 6.6.4 | Folder view, selection, background context menu, Documents navigation and return |
| Thunar | 4.20.9 | Same |
| Caja | 1.26.4 | Same; Caja applies its own tint to selected icons |
| GNOME Files / Nautilus | 51.0.1 | Same |
| PCManFM-Qt | 1.4.1, Qt 5.15.13 | Same, with Qt5ct's icon theme and matching palette selected |

The checks use ordinary-user, isolated D-Bus/Xvfb X11 sessions with real
Cinnamon XSettings and software rendering. They verify preset-colored pixels
and interaction changes, and save screenshots. GTK selection comes from the
desktop settings, without a global `GTK_THEME` override. Qt applications need
working desktop/platform icon integration and an SVG plugin; merely copying
the Qt color palette does not select an icon theme. Native GTK2/3/4 and Qt5/6
lookup/render tests separately cover folder aliases, multiple sizes and
inherited symbolic/application icons.

These results cover the named application versions, not every application or
a complete GNOME, Xfce, MATE, Cinnamon or KDE login session. Native Wayland
file-manager sessions and sandboxed file-manager icon discovery were not
verified in this pass. Applications can deliberately tint selected icons or
use their own artwork; symbolic icons retain upstream Adwaita styling.
See the [reproducible GUI driver](tests/README.md#real-file-manager-folder-icons).

## Reproduced defect and regression checks

The following before/after measurements describe the earlier compatibility fix.
The subsequent readability palette and expanded checks are documented in
[COLOR_READABILITY.md](COLOR_READABILITY.md).

With GTK 4.24.1 / libadwaita 1.10.0 requesting light mode, legacy accent text
resolved to `#1c59cd` on black, approximately **3.36:1** contrast. A destructive
button resolved to `#b91022` on a rendered `#1b0205` background, approximately
**2.99:1**. The modern entry point maps libadwaita's standalone CSS variables
to the existing named AMOLED colors. Accent text becomes `#387af2` (**5.23:1**
on black); the rendered destructive button becomes `#ff7b7b` on `#261212`
(approximately **7.11:1**).

The 14 source/configuration checks and six native checks pass on Ubuntu 24.04
(GTK 4.14 / libadwaita 1.5) and Ubuntu 26.10 (GTK 4.24.1 / libadwaita 1.10.0).
The modern color fixture also passes on GTK 4.18 / libadwaita 1.7.
GitHub Actions checks both the older native stack and an Ubuntu 26.10 container
so that modern-variable regressions are exercised as well.

Additional isolated stress fixtures completed **9,000 window lifecycles and
360,000 click/toggle callbacks** across GTK3, GTK4 and libadwaita, using X11 at
1× and 2×/RTL, and native Wayland with software rendering. No theme parser
errors were recorded. These counters represent automated operations, not a
claim that every application or desktop feature was tested.

## GNOME Shell theme

The separate `gnome-shell/` component keeps all **963 upstream style rules**,
selectors, property names and non-color layout values from Shell 51.1. Its
unmodified upstream Sass and SVG files are pinned by SHA-256 in `UPSTREAM.json`;
the AMOLED palette and local asset paths are applied during a reproducible
build. GNOME's selected system accent hue and privacy indicators are retained.
Subsequent color-only rules darken opaque accent fills by state for readable
white labels; upstream layout remains unchanged.

Four additional checks pass on Shell 51.0 and 51.1. They validate source hashes,
byte-for-byte CSS reproduction, upstream layout preservation and native Shell rendering. Native theme-node
queries confirm black panel, overview, popover and dialog surfaces with white
text, and a `#141414` OSD. Screenshots cover desktop, overview, applications,
quick settings, calendar, a visible notification, volume OSD and modal dialog.
The fixture dismisses startup notifications before testing its own banner and
uses a solid desktop background to avoid distribution wallpaper decoder timing.
This is a logged-in Shell theme for **51.x**, not a GDM resource replacement;
other Shell major versions have not been verified.

## Remaining limits

### GNOME Shell 46 follow-up — 17 October 2026

A user report on GNOME 46 Wayland exposed a version mismatch: the previously
shipped Shell stylesheet targeted 51. Loading it on 46 removes calendar hover
feedback, omits the SVG switch knob and misstyles quick-settings split buttons.
The old stylesheet reproduces the missing calendar hover in a native 46.0 /
Mutter 46.2 headless Wayland session. It remains the negative control for the
new interaction fixture.

A separate AMOLED variant now uses pinned GNOME Shell 46.10 sources and assets,
preserving their geometry and widget structures. Native 46 tests exercise real
pointer motion/clicks and verify panel clock hover/click, calendar hover/selection,
Do Not Disturb off/on images, Show Apps and pinned-app hover, and adjacent split-button allocations. Screenshots are
retained as evidence. The installer selects 46 or 51 from the local Shell version,
rechecks on automatic updates and rejects unsupported explicit Shell setup.
Manual copying must select the matching version-specific stylesheet; source
`gnome-shell.css` remains the 51 default. See [the Shell guide](gnome-shell/README.md).

The Shell 51 fixture also exercises its panel clock, calendar, Show Apps, a pinned
application and split buttons with pointer events. Where the mock power service
does not expose a split button, the fixture inserts GNOME's actual QuickMenuToggle
widget into the menu and records this in its results. Its upstream calendar no longer includes the 46
Do Not Disturb control. This extends interaction coverage without establishing
support for Shell 47–50, extensions that replace these controls, physical GPUs
or complete login sessions.

### Decorative GTK borders — 17 October 2026

The readability update applied `#808080` too broadly to ordinary button frames,
toolbar/header separators and named border aliases. In Cinnamon, Nemo's title
separator, breadcrumb/view buttons and lower toolbar therefore showed bright
outlines; Software Manager's ordinary Gtk.Button package cards inherited the
same borders. These decorative edges now use `#2a2a2a` in GTK3 and plain GTK4,
with matching header/sidebar aliases in the native GTK4/libadwaita overrides.
Text-field and switch boundaries have a separate identifying-control token.
Checkbox/radio borders, slider handles, text colors, accent fills and keyboard
focus remain unchanged.

Native Cairo checks reproduce the bright edge pixels on the previous theme and
verify subtle decorative pixels plus at least 3:1 text-field edge contrast on
the changed theme, including hover/backdrop states. GTK3 focus outline visibility
is checked separately. Actual Nemo 6.6.4 under Cinnamon 6.6.9/Muffin 6.6.3 was
captured before/after: the title separator and multiple toolbar edges changed
from RGB 128 to RGB 42 without changing their geometry. Software Manager's
Gtk.Button card structure is covered by the native fixture; its complete
catalog/backend was not run. The existing text/state/graphic tests remain the
regression guard for controls that still need identifying contrast. Both GTK
resource bundles are rebuilt from the changed source.

Headless Cinnamon and Budgie runs report missing Bluetooth, login/power or
session services. Their stock-theme controls report the same service failures;
Budgie also emits the same `gtk_widget_destroy` assertion with stock Adwaita.
An initial Cinnamon run additionally logged a grouped-window-list startup
exception with a null workspace. It was not established as a stylesheet defect;
the same themed test completed without that exception after waiting for
Cinnamon's `RunState.RUNNING` before starting clients. Startup timing and
complete desktop-service behavior remain outside a clean
end-to-end claim. No upstream desktop code was changed.

The Shell fixture similarly reports missing IBus, authentication and volume
services, plus a GDM registration signature mismatch in the upstream mock.
It does not establish working screen locking; GNOME explicitly reports that
screen locking requires GDM in this isolated session. These service boundaries
are separate from the passing stylesheet and rendering checks.

There is no physical OLED panel, DRM/GPU device or real login seat in this
environment. Hardware drivers, power savings, HDR, burn-in behavior, login,
locking and suspend are unverified. Flatpak sandbox execution remains blocked
by the environment's namespace restrictions. Budgie's built-in-theme-disabled
configuration, native Wayland Cinnamon/Xfce sessions, and a full GNOME/MATE
login session were not verified.

## Official references

- [GNOME 51 build manifest](https://github.com/GNOME/gnome-build-meta/tree/51.0)
  and [Shell 51.1 NEWS](https://github.com/GNOME/gnome-shell/blob/51.1/NEWS)
- [GTK 4.24.1 styles](https://github.com/GNOME/gtk/tree/4.24.1/gtk/theme/Default)
  and [GTK 3.24.52 NEWS](https://github.com/GNOME/gtk/blob/3.24.52/NEWS)
- [libadwaita 1.10 styles](https://github.com/GNOME/libadwaita/tree/1.10.0/src/stylesheet)
  and [1.6 CSS-variable migration notes](https://github.com/GNOME/libadwaita/blob/1.10.0/NEWS)
- [Cinnamon 6.6.9 styles](https://github.com/linuxmint/cinnamon/tree/6.6.9/data/theme/cinnamon-sass)
- [Xfce panel 4.20.8 NEWS](https://github.com/xfce-mirror/xfce4-panel/blob/xfce4-panel-4.20.8/NEWS)
- [MATE 1.28 release announcement](https://github.com/mate-desktop/mate-desktop.org/blob/master/blog/20240227-mate-1-28-released.md)
  and [Marco 1.28.2](https://github.com/mate-desktop/marco/tree/v1.28.2)
- [Budgie 10.10.3 release](https://github.com/BuddiesOfBudgie/budgie-desktop/releases/tag/v10.10.3)
