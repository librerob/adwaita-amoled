# Repository-wide color follow-up — 2026-10-16

The optional seven-color presets and their measurements are documented in
[Accent presets](ACCENT_COLORS.md). The blue-theme findings below remain historical.

**17 October follow-up:** decorative button/card frames, header/sidebar and
toolbar separators now use the subtle border palette after a Cinnamon user
report showed that identifying-control brightness had been applied too broadly.
Input edges, checkbox/radio outlines, slider handles and focus retain their
separate visibility roles. Native before/after evidence and current regression
coverage are described in [the compatibility report](COMPATIBILITY.md#decorative-gtk-borders--17-october-2026).
The measurements below record the earlier audit rather than every subsequent
appearance change.

This follow-up starts from v1.2.0 (`ed1c29b63f2312e2818145e0f10cf5f59c4be3e9`).
The earlier readability tests passed, but their coverage missed several inherited
and compound states. The new tests reproduce those failures against v1.2.0 and
check the fixes against native consumers. With the expanded fixtures, v1.2.0
fails 103 of the 241 GTK3 context pairs, 21/33 GTK3 and 18/33 plain GTK4
selected-row pairs, 274/936 Shell control/glyph pairs, and 12/125 Cinnamon
pairs. These overlapping counts are not counts of distinct bugs.
Passing the previous suite did not
mean every color combination was correct.

Scope: **librerob/adwaita-amoled only**. All 186 files in the starting revision
were inventoried, including source, generated styles, binary resources, SVG/XML
paints, application palettes, tests, documentation and artwork. The proposed
revision has 189 files: two new native regression helpers and this report.
No other repository, existing release, tag or issue is part of this update.

## Confirmed failures and fixes

Ratios below use native resolved colors and alpha composition. Ordinary enabled
text is checked at 4.5:1; identifying graphics and focus indicators at 3:1.
Figures are rounded here; test evidence retains the full measurements.

| Trigger | Before | After / change |
| --- | --- | --- |
| GTK3 selected row while hovered | White on pale hover blue: 1.65:1 | Separate dark fill-hover blue `#2862cf`: 5.62:1 |
| GTK3 checked/indeterminate checkbox or radio while hovered | White mark: 1.65:1 | Dark hover fill; representative mark pair 5.62:1 |
| GTK3 secondary label in a selected row | Dimmed text: 2.55:1 | Full-opacity selection text: 4.89:1 |
| GTK3 flat action in a selected backdrop row | Gray on blue: 2.69:1 | White selection foreground: 4.89:1 |
| GTK4 selected-row semantic/link/flat-action text | Status ink and inherited backdrop labels lose contrast | Explicit selection foreground, including button child labels; 33 selected-row pairs pass |
| GTK3 focus outline on selected-row flat action | Pale accent on blue: 2.32:1 | White inset focus outline: 4.89:1 |
| GTK3 adjacent-month calendar dates | Selectable dates: 1.21:1 | Opaque secondary ink: 8.03:1 |
| GTK3 enabled notebook close glyph | Faded glyph: 2.62:1 | Secondary ink: 7.48:1 in the measured resting state |
| GTK3 checked content-view control in backdrop | 1.94:1 | Dark blue fill: 3.27:1, exceeding the graphic threshold |
| GTK3 selection-header arrow and subtitle | Half-opacity arrow/secondary text on selection blue | Opaque selection ink; tested separately in backdrop states |
| GTK3 selected sidebar drop target | White on bright green: 2.12:1 | Black selection ink on the same green |
| GTK3 print preview page numbers | White on white: 1:1 | `#757575` ink: 4.61:1 on paper; black preview canvas gives rulers 4.56:1 |
| GTK3 legacy error-color alias | Pure red loses 4.5:1 on some raised surfaces | Existing light error ink also used by the alias |
| GTK4/libadwaita flat semantic suggested action | Generic blue overrides success/warning/error ink | Restore each enabled action's named standalone status color |
| Shell checked menu button with active + focus | Compound-state rules could restore a lighter fill | Explicit darker pressed fill |
| Shell checkbox/switch, including Looking Glass switches | Warm accent hover could leave a white mark/handle at 2.40:1 | Darker checked fills; Looking Glass specificity covered separately |
| Shell calendar week number and keyboard suggestion states | Small text or light neutral fills fall below 4.5:1 | Secondary week-number ink and darker suggestion fills |
| Shell resting scrollbar thumb | About 2.48:1 against black | Visible neutral thumb; all 162 measured graphic pairs exceed 3:1 |
| Shell message placeholder with smaller font | 4.43:1 with 9-point interface font, below ordinary-text threshold | Opaque secondary ink; 9/11/14-point probes pass |
| Cinnamon task label with progress/attention overlay | 12 failures among 125 pairs; minimum 2.12:1 | Reduce progress-fill opacity and preserve white attention text, including running state; all 125 pass, minimum 4.89:1 |

GTK uses the same print-preview ink for page numbers and outside rulers. A black
ink would hide those rulers. The chosen gray and black preview canvas meet 4.5:1
on both surfaces. The native print dialog shows the page number and rulers;
printer-dependent settings, actual printing and every number-up layout were not
available in this environment.

The main accent roles remain separate: pale blue `#8ab4f8` for standalone text,
`#aecbfa` for text hover, dark blue `#2d6be0` behind white labels, and `#2862cf`
for filled hover states. Existing pale editor/Qt selections keep dark text.
Selected opaque GTK rows use selection text instead of semantic hues; libadwaita's
darker translucent row selection keeps its independently readable status hues.
GNOME Shell retains all nine system accent hues. Pinned upstream Sass and SVGs
remain unchanged; adaptations live outside the pinned source directory.

## Accounting for every file and color role

The accompanying audit evidence contains a SHA-256/git-blob inventory for every
file, line/column records for color literals and functions, parsed CSS/QSS/Rofi
color-related declarations, SVG paint/opacity properties with XML source lines,
and separate Metacity/GTK2 role ledgers. Literal enumeration also sees comments,
examples and SVG editor metadata; those records are not automatically live paint.
Native probes resolve named colors, Sass-generated values, inheritance and alpha
that cannot be judged from a hex search.

| Files / subsystem | Review and evidence |
| --- | --- |
| GTK3 source and entry points | Native parser, Cairo backgrounds, widget text/opacity, selector diagnostics, real calendar/row/check/notebook screenshots |
| GTK4/plain and libadwaita source/overrides | Native light/dark scheme requests, GSK text/opacity nodes, named status roles, selected-row descendants |
| Both binary GResources | Rebuilt from the changed source; extracted shipping and fresh resource contents compared with source by the regression suite |
| GNOME Shell source, generated CSS and six SVGs | All 50 pinned upstream source/asset hashes unchanged; reproducible Sass output; all 963 upstream layout rules retained; native Shell at 1×/2× |
| Cinnamon CSS, 43 SVGs and two UI PNGs | Parsed paint/opacity ledger, native St roles/overlays, full SVG rendering/gallery review; grayscale PNG cores and alpha reviewed |
| GTK2 RC | All 23 styles and inherited state tables: 230 pairs recorded, 168 enabled text pairs checked; native Murrine representative control paints |
| Metacity XML | Every color/alpha declaration inventoried; 58 title/glyph/layer pairs checked; native renderer exercises 504 frame combinations |
| Openbox palette and four XBM masks | Enabled titles/menu labels and action glyphs checked; monochrome masks use the palette's image colors |
| Qt5ct / Qt6ct colors and QSS | All scheme entries inventoried, active/inactive roles and placeholders checked natively, scrollbar identifying paints reviewed |
| Neovim / Airline | 736 resolved editor pairs and 70 true-color/256-color Airline pairs through the real plugins |
| Alacritty / Kitty / Zsh | All defined colors reviewed by role; normal/bright/dim text, opacity, selections, search, cursor, tabs and completion pairs checked |
| bat and Rofi | All bat syntax foregrounds checked on supported backgrounds and native cache built; native Rofi parser and inherited selection/text roles reviewed |
| Symbolic SVG copies | All 12 copies accounted for; native parsing/rendering and resource/copy consistency checked; runtime foreground can replace template paint |
| Four artwork PNGs | Logo, wallpaper and historical screenshots recorded and retained as artwork |
| Build files, tests, licenses and documentation | Accounted for separately; fixture colors, upstream references and historical examples are not shipped UI foreground roles |

Supplemental diagnostics evaluated 1,434 GTK3 CSS-node contexts, 1,713 Shell
selector contexts across nine accents (15,417 probes), and 466 Cinnamon contexts.
These are diagnostic selector constructions, not 17,317 real application widgets.
They helped find missing states; they do not exhaust all possible descendants,
font settings or application CSS. Shell sibling-dependent selectors are marked as
relationally unverified where the native ThemeNode API cannot supply siblings.
Image-backed and application-painted surfaces require separate interpretation.

Low foreground ratios on empty slider/progress actors are not text failures:
the visible object is their background paint, which must be compared with its
surrounding surface. Other reviewed candidates include hidden spinners, unchecked
marks, decorative separators, disabled controls, empty drag placeholders and
color-picker overlays on application-selected colors. The evidence records those
classifications instead of silently treating every candidate as a passed text pair.

## Regression coverage

The five automated suites now contain **50 tests**: 14 source/install checks,
10 readability checks, 16 GTK/libadwaita/Metacity runtime checks, six additional
consumer checks and four Shell checks. The separate Cinnamon integration fixture
now also runs in its own CI job. Commands and packages are in
[tests/README.md](tests/README.md).

- 1,199 representative GTK color/state measurements; 109 disabled samples
  recorded separately. Enabled text must meet 4.5:1.
- 241 additional GTK3 inherited/compound/context pairs, with role-specific text,
  graphic, focus, named-color and print-preview thresholds.
- 33 actual selected-row/descendant pairs for each of GTK3, plain GTK4,
  libadwaita dark and libadwaita light: 132 pairs total.
- 936 Shell control/glyph pairs across nine accents; minimum 4.53:1.
  Another 162 scrollbar graphic pairs have a minimum of 4.41:1; three
  placeholder font-size pairs pass. Headless native Wayland tested with
  packaged Shell 51.0 and built upstream 51.1, with eight views and 40 transitions.
- 125 Cinnamon text/state/overlay pairs pass, with 2,421 style queries.
  Nonuniform gradients are sampled at both ends and 31 interior points.
- All 61 SVGs render with librsvg. Native GTK2/Murrine, Qt5/6, bat, Rofi,
  Neovim/Airline, Kitty, Zsh, installation and resource checks remain covered.

## Limits

This is complete repository-file accounting plus substantially broader native
color testing. It is **not proof that every possible color combination is
perfect**, or that the theme is bug-free or fully WCAG conformant.

Decorative surface borders and shadows can intentionally be faint. Disabled
controls are recorded separately. SVG editor metadata, template mask paints and
unused upstream light/high-contrast branches are not all runtime AMOLED colors.
ANSI normal/dim black can intentionally match a black background. Applications
can supply arbitrary foregrounds, opacity, backgrounds, icons and custom CSS.
Antialiased edges are not required to meet the solid-interior ratio independently.

Physical OLED/GPU output, PWM, reflections, subpixel rendering, power and panel
lifetime remain unverified. Brave, Flatpak, real login/lock/suspend and complete
interactive GNOME/Xfce/Cinnamon/MATE/Budgie sessions are also outside this audit's
verified coverage. Software/native toolkit results cannot establish those claims.
