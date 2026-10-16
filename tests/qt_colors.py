import configparser, importlib, json, os, sys, time
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
version, root, output = sys.argv[1:]
root = Path(root)
out = Path(output)
out.mkdir(parents=True, exist_ok=True)
Q = importlib.import_module("PyQt" + version + ".QtWidgets")
G = importlib.import_module("PyQt" + version + ".QtGui")
app = Q.QApplication([])
app.setStyle("Fusion")
palette = G.QPalette()
config = configparser.ConfigParser()
config.read(root / f"extra/qt{version}ct/colors/Adwaita-AMOLED.conf")
for group, key in [
    (G.QPalette.ColorGroup.Active, "active_colors"),
    (G.QPalette.ColorGroup.Inactive, "inactive_colors"),
    (G.QPalette.ColorGroup.Disabled, "disabled_colors"),
]:
    for role, color in enumerate(config["ColorScheme"][key].split(",")):
        palette.setColor(group, G.QPalette.ColorRole(role), G.QColor(color.strip()))
app.setPalette(palette)
app.setStyleSheet(
    (root / f"extra/qt{version}ct/qss/fusion-simple-scrollbar.qss").read_text()
)
w = Q.QWidget()
layout = Q.QVBoxLayout(w)
layout.addWidget(Q.QLabel("Native Qt " + version + " AMOLED palette"))
for placeholder in [False, True]:
    e = Q.QLineEdit()
    e.setPlaceholderText("Readable placeholder")
    if not placeholder:
        e.setText("Readable text and selection")
        e.selectAll()
    layout.addWidget(e)
layout.addWidget(Q.QPushButton("A readable button"))
listing = Q.QListWidget()
listing.addItems(["First item", "Selected item", "Third item"])
listing.setCurrentRow(1)
layout.addWidget(listing)
w.resize(440, 340)
w.show()
for _ in range(10):
    app.processEvents()
    time.sleep(0.02)
w.grab().save(str(out / f"qt{version}.png"))
pairs = []


def rgb(c):
    return [c.red(), c.green(), c.blue()]


def lum(c):
    return sum(
        (v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
        * weight
        for v, weight in zip(c, [0.2126, 0.7152, 0.0722])
    )


for group in [G.QPalette.ColorGroup.Active, G.QPalette.ColorGroup.Inactive]:
    for fg, bg in [
        (0, 10),
        (6, 9),
        (8, 1),
        (13, 12),
        (14, 9),
        (15, 9),
        (19, 18),
        (20, 9),
    ]:
        foreground = palette.color(group, G.QPalette.ColorRole(fg))
        background = palette.color(group, G.QPalette.ColorRole(bg))
        f = [
            round(v * foreground.alphaF() + b * (1 - foreground.alphaF()))
            for v, b in zip(rgb(foreground), rgb(background))
        ]
        b = rgb(background)
        ratio = (max(lum(f), lum(b)) + 0.05) / (min(lum(f), lum(b)) + 0.05)
        pairs.append(
            {
                "group": group.value if hasattr(group, "value") else int(group),
                "foreground_role": fg,
                "background_role": bg,
                "foreground": f,
                "background": b,
                "contrast": ratio,
            }
        )
(out / f"qt{version}.json").write_text(json.dumps(pairs, indent=2) + "\n")
assert all(p["contrast"] >= 4.5 for p in pairs), pairs
print(
    json.dumps(
        {
            "qt": version,
            "pairs": len(pairs),
            "minimum_contrast": min(p["contrast"] for p in pairs),
        }
    )
)
w.close()
