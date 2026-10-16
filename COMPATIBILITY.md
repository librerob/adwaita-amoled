# Upstream compatibility review — 16 October 2026

The GTK and libadwaita theme was compared with the current stable upstream
styles and exercised with native consumers. One compatibility defect was
reproduced and addressed: modern libadwaita derives standalone text colors from
the requested light/dark scheme, while the AMOLED override keeps surfaces dark.
The legacy overrides alone could therefore produce dark text on black.

Use the modern entry point described in [the installation instructions](README.md#gtk4--libadwaita)
on GTK 4.16 or newer. Keep the legacy entry point on older GTK releases.

## Versions and coverage

| Component | Stable target checked | Evidence and boundary |
| --- | --- | --- |
| GNOME | 51; Shell 51.1 | Official release sources and GNOME 51 toolkit manifest reviewed. Application styling tested through GTK/libadwaita below. This repository has no GNOME Shell stylesheet; the GNOME Shell session itself was not run. |
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

## Reproduced defect and regression checks

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

## Remaining limits

Headless Cinnamon and Budgie runs report missing Bluetooth, login/power or
session services. Their stock-theme controls report the same service failures;
Budgie also emits the same `gtk_widget_destroy` assertion with stock Adwaita.
An initial Cinnamon run additionally logged a grouped-window-list startup
exception with a null workspace. It was not established as a stylesheet defect;
the same themed test completed without that exception after waiting for
Cinnamon's `RunState.RUNNING` before starting clients. Startup timing and
complete desktop-service behavior remain outside a clean
end-to-end claim. No upstream desktop code was changed.

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
