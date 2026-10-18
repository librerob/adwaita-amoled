"""Paint actual Fusion slider handles and exercise pointer/keyboard interaction."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

version, source, output = sys.argv[1:4]
root, out = Path(source), Path(output)
if len(sys.argv) == 4:
    for scale in (1, 2):
        result = subprocess.run(
            [sys.executable, __file__, version, source, output, str(scale)],
            env=dict(
                os.environ, QT_QPA_PLATFORM="offscreen", QT_SCALE_FACTOR=str(scale)
            ),
            capture_output=True,
            text=True,
            timeout=25,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout.strip())
    sys.exit(0)

import configparser

Q = importlib.import_module("PyQt" + version + ".QtWidgets")
G = importlib.import_module("PyQt" + version + ".QtGui")
C = importlib.import_module("PyQt" + version + ".QtCore")
T = importlib.import_module("PyQt" + version + ".QtTest")
app = Q.QApplication([])
app.setStyle("Fusion")
config = configparser.ConfigParser()
config.read(root / f"extra/qt{version}ct/colors/Adwaita-AMOLED.conf")
palette = G.QPalette()
for group, key in [
    (G.QPalette.ColorGroup.Active, "active_colors"),
    (G.QPalette.ColorGroup.Inactive, "inactive_colors"),
    (G.QPalette.ColorGroup.Disabled, "disabled_colors"),
]:
    for role, color in enumerate(config["ColorScheme"][key].split(",")):
        palette.setColor(group, G.QPalette.ColorRole(role), G.QColor(color.strip()))
app.setPalette(palette)
qss = (root / f"extra/qt{version}ct/qss/fusion-simple-scrollbar.qss").read_text()
out.mkdir(parents=True, exist_ok=True)


def pump():
    for _ in range(5):
        app.processEvents()
        time.sleep(0.002)


def handle(slider):
    option = Q.QStyleOptionSlider()
    slider.initStyleOption(option)
    return slider.style().subControlRect(
        Q.QStyle.ComplexControl.CC_Slider,
        option,
        Q.QStyle.SubControl.SC_SliderHandle,
        slider,
    )


def rgb(color):
    return [color.red(), color.green(), color.blue()]


def luminance(channels):
    return sum(
        (v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
        * weight
        for v, weight in zip(channels, (0.2126, 0.7152, 0.0722))
    )


rows = []
for orientation in ("horizontal", "vertical"):
    for surface in (0, 30):
        for state in ("normal", "hover", "focus", "pressed", "inactive", "disabled"):
            app.setStyleSheet("")
            parent = Q.QWidget()
            parent.resize(500, 400)
            sibling = Q.QPushButton("Other focus target", parent)
            sibling.move(300, 350)
            slider = Q.QSlider(
                (
                    C.Qt.Orientation.Horizontal
                    if orientation == "horizontal"
                    else C.Qt.Orientation.Vertical
                ),
                parent,
            )
            slider.setGeometry(
                20, 20, *((400, 64) if orientation == "horizontal" else (64, 300))
            )
            slider.setAutoFillBackground(True)
            p = G.QPalette(palette)
            for group in (
                G.QPalette.ColorGroup.Active,
                G.QPalette.ColorGroup.Inactive,
                G.QPalette.ColorGroup.Disabled,
            ):
                p.setColor(
                    group,
                    G.QPalette.ColorRole.Window,
                    G.QColor(surface, surface, surface),
                )
            slider.setPalette(p)
            slider.setValue(50)
            parent.show()
            parent.activateWindow()
            app.setActiveWindow(parent)
            sibling.setFocus()
            T.QTest.mouseMove(sibling)
            pump()
            before = handle(slider)
            app.setStyleSheet(qss)
            pump()
            rect = handle(slider)
            assert rect == before, (
                version,
                orientation,
                "native handle geometry changed",
                rect,
                before,
            )
            if state in ("hover", "pressed"):
                T.QTest.mouseMove(slider, rect.center())
            if state == "focus":
                slider.setFocus()
            if state == "pressed":
                T.QTest.mousePress(
                    slider, C.Qt.MouseButton.LeftButton, pos=rect.center()
                )
                assert slider.isSliderDown()
            if state == "disabled":
                slider.setEnabled(False)
            if state == "inactive":
                app.setActiveWindow(None)
            pump()
            image = slider.grab().toImage()
            ratio = image.devicePixelRatio()
            point = rect.center()
            if orientation == "horizontal":
                point.setY(rect.top() + rect.height() // 4)
            else:
                point.setX(rect.left() + rect.width() // 4)
            fg = rgb(
                image.pixelColor(round(point.x() * ratio), round(point.y() * ratio))
            )
            bg = rgb(image.pixelColor(0, 0))
            f, b = luminance(fg), luminance(bg)
            contrast = (max(f, b) + 0.05) / (min(f, b) + 0.05)
            row = dict(
                orientation=orientation,
                surface=surface,
                state=state,
                handle=fg,
                background=bg,
                contrast=contrast,
                geometry=[rect.x(), rect.y(), rect.width(), rect.height()],
            )
            rows.append(row)
            if state != "disabled":
                assert contrast >= 3, row
            if state == "pressed":
                T.QTest.mouseRelease(
                    slider, C.Qt.MouseButton.LeftButton, pos=rect.center()
                )
                assert not slider.isSliderDown()
            slider.setEnabled(True)
            slider.setFocus()
            if state == "normal":
                value = slider.value()
                start = handle(slider).center()
                end = start + (
                    C.QPoint(40, 0) if orientation == "horizontal" else C.QPoint(0, -40)
                )
                T.QTest.mousePress(slider, C.Qt.MouseButton.LeftButton, pos=start)
                event = G.QMouseEvent(
                    C.QEvent.Type.MouseMove,
                    C.QPointF(end),
                    C.QPointF(slider.mapToParent(end)),
                    C.QPointF(slider.mapToGlobal(end)),
                    C.Qt.MouseButton.NoButton,
                    C.Qt.MouseButton.LeftButton,
                    C.Qt.KeyboardModifier.NoModifier,
                )
                app.sendEvent(slider, event)
                T.QTest.mouseRelease(slider, C.Qt.MouseButton.LeftButton, pos=end)
                assert slider.value() > value, "Native drag stopped changing the value"
            value = slider.value()
            T.QTest.keyClick(
                slider,
                C.Qt.Key.Key_Right if orientation == "horizontal" else C.Qt.Key.Key_Up,
            )
            assert slider.value() == value + 1
            if surface == 0 and state in ("normal", "hover", "focus", "pressed"):
                image.save(
                    str(
                        out
                        / f"qt{version}-{orientation}-{state}-scale{sys.argv[4]}.png"
                    )
                )
            parent.close()

(out / f"qt{version}-sliders-scale{sys.argv[4]}.json").write_text(
    json.dumps(rows, indent=2) + "\n"
)
print(
    json.dumps(
        {
            "qt": version,
            "scale": int(sys.argv[4]),
            "native_slider_samples": len(rows),
            "minimum_enabled_contrast": min(
                r["contrast"] for r in rows if r["state"] != "disabled"
            ),
        }
    )
)
