import json, os, subprocess, sys, tempfile, time
from pathlib import Path
import gi
from gi.repository import Gio, GLib

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="amoled-colors-cinnamon-") as temporary:
    home = Path(temporary)
    env = dict(
        os.environ,
        HOME=str(home),
        GSETTINGS_BACKEND="keyfile",
        GTK_THEME="Adwaita-AMOLED",
        LIBGL_ALWAYS_SOFTWARE="1",
        CLUTTER_BACKEND="x11",
        GDK_BACKEND="x11",
        XDG_SESSION_TYPE="x11",
        XDG_CURRENT_DESKTOP="X-Cinnamon",
    )
    for name, directory in [
        ("XDG_DATA_HOME", "data"),
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_CACHE_HOME", "cache"),
        ("XDG_RUNTIME_DIR", "runtime"),
    ]:
        p = home / directory
        p.mkdir()
        p.chmod(0o700)
        env[name] = str(p)
    themes = home / "data/themes"
    themes.mkdir()
    (themes / "Adwaita-AMOLED").symlink_to(root)
    subprocess.run(
        ["gsettings", "set", "org.cinnamon.theme", "name", "Adwaita-AMOLED"],
        env=env,
        check=True,
    )
    subprocess.run(
        [
            "gsettings",
            "set",
            "org.cinnamon.desktop.interface",
            "gtk-theme",
            "Adwaita-AMOLED",
        ],
        env=env,
        check=True,
    )
    with (out / "session.log").open("w") as log:
        process = subprocess.Popen(
            ["cinnamon-session", "--session", "cinnamon", "--debug"],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            proxy = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.Cinnamon",
                "/org/Cinnamon",
                "org.Cinnamon",
                None,
            )

            def evaluate(source):
                success, result = proxy.call_sync(
                    "Eval",
                    GLib.Variant("(s)", (source,)),
                    Gio.DBusCallFlags.NONE,
                    10000,
                    None,
                ).unpack()
                assert success, result
                return result

            for _ in range(200):
                assert process.poll() is None, "Cinnamon exited; see session.log"
                try:
                    if (
                        json.loads(
                            evaluate(
                                'imports.ui.main.runState === imports.ui.main.RunState.RUNNING ? "READY" : "STARTING"'
                            )
                        )
                        == "READY"
                    ):
                        break
                except GLib.Error:
                    pass
                time.sleep(0.1)
            else:
                raise AssertionError("Cinnamon did not become ready")
            source = r"""(() => {
    const St=imports.gi.St,context=St.ThemeContext.get_for_stage(global.stage),theme=context.get_theme();
    const node=(parent,id,classes,state)=>St.ThemeNode.new(context,parent,theme,St.Widget.$gtype,id,classes,state,'',false);
    const colors=[];
    for (const [name,parentClass,classes,baseState] of [
      ['dialog-default','dialog','dialog-button','default'],
      ['dialog-destructive','dialog','dialog-button','destructive-action'],
      ['dialog-normal','dialog','dialog-button',''],
      ['menu-item','popup-menu','popup-menu-item',''],
      ['entry',null,'entry',''],
      ['prompt-error',null,'prompt-dialog-error-label',''],
      ['run-error','run-dialog','run-dialog-description error',''],
      ['panel-warning',null,'system-status-icon warning',''],
      ['panel-error',null,'system-status-icon error',''],
      ['calendar-day','calendar','calendar-day',''],
      ['dialog-description','dialog-list','dialog-list-item-description',''],
    ]) {
      for (const state of ['', 'hover','active','checked','focus','focus hover','active hover']) {
        let parent=context.get_root_node();
        if(parentClass)parent=node(parent,null,parentClass,null);
        const n=node(parent,null,classes,[baseState,state].filter(Boolean).join(' '));
        colors.push({name,state,foreground:n.get_foreground_color().to_string(),background:n.get_background_color().to_string()});
      }
    }
    let styleNodes=0;
    {
      for (const cls of CLASS_NAMES) {
        for (const state of ['', 'hover','active','checked','focus','insensitive','rtl','selected','checked hover']) {
          const n=node(context.get_root_node(),null,cls,state);
          n.get_background_color(); n.get_foreground_color(); n.get_background_image();
          n.get_border_image(); n.get_font(); n.get_box_shadow();
          styleNodes++;
        }
      }
    }
    return {directory:imports.ui.main.themeManager.themeDirectory,colors,styleNodes};
   })()"""
            import re

            classes = sorted(
                set(
                    re.findall(
                        r"(?<![\w.])\.([a-zA-Z_][\w-]*)",
                        (root / "cinnamon/cinnamon.css").read_text(),
                    )
                )
            )
            source = source.replace("CLASS_NAMES", json.dumps(classes))
            source = (
                "(() => {try {return "
                + source
                + ";} catch(e) {return {error: String(e), stack:e.stack};}})()"
            )
            result = json.loads(evaluate(source))
            assert "error" not in result, result
            assert result["directory"].endswith("Adwaita-AMOLED/cinnamon"), result[
                "directory"
            ]

            def rgb(s):
                return [int(s[i : i + 2], 16) for i in (1, 3, 5)]

            def composite(s, b):
                alpha = int(s[7:9], 16) / 255
                return [round(c * alpha + v * (1 - alpha)) for c, v in zip(rgb(s), b)]

            def lum(c):
                return sum(
                    (
                        v / 255 / 12.92
                        if v / 255 <= 0.04045
                        else ((v / 255 + 0.055) / 1.055) ** 2.4
                    )
                    * w
                    for v, w in zip(c, [0.2126, 0.7152, 0.0722])
                )

            for pair in result["colors"]:
                # Image-backed popup/dialog cards use the theme's opaque #141414 base.
                bg = composite(pair["background"], [20, 20, 20])
                fg = composite(pair["foreground"], bg)
                pair["composited_background"] = bg
                pair["contrast"] = (max(lum(fg), lum(bg)) + 0.05) / (
                    min(lum(fg), lum(bg)) + 0.05
                )
            (out / "colors.json").write_text(json.dumps(result, indent=2) + "\n")
            failed = [p for p in result["colors"] if p["contrast"] < 4.5]
            print(
                json.dumps(
                    {
                        "pairs": len(result["colors"]),
                        "style_nodes": result["styleNodes"],
                        "failures": failed,
                        "minimum_contrast": min(
                            p["contrast"] for p in result["colors"]
                        ),
                    }
                )
            )
            assert not failed, failed
            subprocess.run(
                [
                    "python3",
                    str(root / "tests/native.py"),
                    "--capture",
                    str(out / "cinnamon.png"),
                ],
                env=env,
                check=True,
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
