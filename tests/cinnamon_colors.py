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
        {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("GH_", "GITHUB_", "ACTIONS_"))
            and "TOKEN" not in key
            and "SECRET" not in key
        },
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
    // Progress fills are painted behind sibling labels in both task applets.
    // Resolve both layers, including attention gradients, instead of treating
    // the empty progress actor's foreground as visible text.
    const mix=(fg,bg)=>{
      const a=parseInt(fg.slice(7,9),16)/255;
      return '#'+[1,3,5].map(i=>Math.round(parseInt(fg.slice(i,i+2),16)*a+
        parseInt(bg.slice(i,i+2),16)*(1-a)).toString(16).padStart(2,'0')).join('')+'ff';
    };
    for(const [task,attention] of [
      ['window-list-item-box','window-list-item-demands-attention'],
      ['grouped-window-list-item-box','grouped-window-list-item-demands-attention'],
    ]) {
      const panel=node(context.get_root_node(),'panel',null,null);
      for(const state of ['', 'running','hover','active','checked','focus']) {
        for(const urgent of [false,true]) {
          const button=node(panel,null,[task,urgent?attention:''].filter(Boolean).join(' '),state);
          const label=St.ThemeNode.new(context,button,theme,St.Label.$gtype,null,null,null,'',false);
          let background=mix(button.get_background_color().to_string(),panel.get_background_color().to_string());
          const gradient=button.get_background_gradient();
          let backgrounds=[background];
          if(gradient[0]!==0) {
            const start=gradient[1].to_string(),end=gradient[2].to_string();
            // Include both endpoints and the interior of nonuniform gradients.
            backgrounds=Array.from({length:33},(_,i)=>{
              const t=i/32;
              const color='#'+[1,3,5,7].map(k=>Math.round(parseInt(start.slice(k,k+2),16)*(1-t)+
                parseInt(end.slice(k,k+2),16)*t).toString(16).padStart(2,'0')).join('');
              return mix(color,background);
            });
          }
          for(const progress of [false,true]) {
            const fill=node(button,null,'progress',null);
            colors.push({name:task+(urgent?'-attention':'')+(progress?'-progress':''),state,
              foreground:label.get_foreground_color().to_string(),
              background:backgrounds[0],
              backgrounds:backgrounds.map(bg=>progress?mix(fill.get_background_color().to_string(),bg):bg)});
          }
        }
      }
    }
    const decorativeBorders=[];
    for(const [name,id,classes] of [
      ['tooltip','Tooltip',null],
      ['notification','notification',null],
      ['task-preview',null,'window-list-preview'],
      ['grouped-task-preview',null,'grouped-window-list-thumbnail-menu'],
      ['start-sidebar',null,'appmenu-sidebar'],
    ]) {
      for(const state of ['', 'hover','focus','active']) {
        const n=node(context.get_root_node(),id,classes,state);
        decorativeBorders.push({name,state,widths:[0,1,2,3].map(side=>n.get_border_width(side)),
          colors:[0,1,2,3].map(side=>n.get_border_color(side).to_string())});
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
    return {directory:imports.ui.main.themeManager.themeDirectory,colors,styleNodes,decorativeBorders};
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
                backgrounds = [
                    composite(color, [20, 20, 20])
                    for color in pair.get("backgrounds", [pair["background"]])
                ]
                pair["composited_backgrounds"] = backgrounds
                pair["contrast"] = min(
                    (max(lum(composite(pair["foreground"], bg)), lum(bg)) + 0.05)
                    / (min(lum(composite(pair["foreground"], bg)), lum(bg)) + 0.05)
                    for bg in backgrounds
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
            for sample in result["decorativeBorders"]:
                expected = [0, 1, 0, 0] if sample["name"] == "start-sidebar" else [1, 1, 1, 1]
                assert sample["widths"] == expected, sample
                for width, color in zip(sample["widths"], sample["colors"]):
                    if width:
                        assert color == "#2a2a2aff", sample
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
