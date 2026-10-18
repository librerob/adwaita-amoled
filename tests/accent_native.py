"""Run native consumer regressions against each materialized accent preset.

Development/CI only: pass a consumer group and an evidence directory. Each
variant shares the unchanged runtime files and overlays only its own colors.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COLORS = ("yellow", "gold", "purple", "green", "red", "orange", "pink")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "group",
        choices=("gtk", "qt", "edges", "extras", "cinnamon", "shell46", "shell51"),
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--colors", nargs="+", choices=COLORS, default=COLORS)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for color in args.colors:
        evidence = output / color
        evidence.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"amoled-native-{color}-") as temporary:
            root = Path(temporary) / "Adwaita-AMOLED"
            for name in (ROOT / "runtime-files.txt").read_text().splitlines():
                source = ROOT / "accents" / color / name
                if not source.is_file():
                    source = ROOT / name
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            shutil.copytree(
                ROOT / "tests",
                root / "tests",
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            # bat's existing syntax fixture highlights this development script.
            shutil.copy2(ROOT / "build.sh", root / "build.sh")
            tests = root / "tests"
            if args.group == "gtk":
                commands = [
                    [str(tests / "gtk2_colors.py"), str(root), str(evidence / "gtk2")],
                    [
                        str(tests / "gtk3_color_states.py"),
                        str(root),
                        str(evidence / "gtk3-states"),
                    ],
                ]
                for consumer in ("gtk3", "gtk4", "adw"):
                    for mode in ([], ["--light"]):
                        label = consumer + ("-light" if mode else "-dark")
                        commands.append(
                            [
                                str(tests / "color_native.py"),
                                str(root),
                                consumer,
                                str(evidence / label),
                                *mode,
                            ]
                        )
                        commands.append(
                            [
                                str(tests / "selection_colors.py"),
                                str(root),
                                "3.0" if consumer == "gtk3" else "4.0",
                                str(evidence / (label + "-selection")),
                                *(["--adw"] if consumer == "adw" else []),
                                *mode,
                            ]
                        )
            elif args.group == "qt":
                commands = [
                    [
                        str(tests / script),
                        version,
                        str(root),
                        str(evidence / (script.removesuffix(".py") + version)),
                    ]
                    for version in ("5", "6")
                    for script in ("qt_colors.py", "qt_sliders.py")
                ]
            elif args.group == "edges":
                commands = [[str(tests / "test_borders.py")]]
            elif args.group == "extras":
                commands = [
                    [
                        str(tests / "test_theme.py"),
                        "ThemeTests.test_zsh_clean_shell_and_existing_hooks",
                        "ThemeTests.test_kitty_native_config",
                        "ThemeTests.test_zsh_preserves_interactive_completion",
                        "ThemeTests.test_neovim_colorscheme",
                    ],
                    [
                        str(tests / "test_consumers.py"),
                        "ConsumerTests.test_bat_native_theme_cache_and_highlighting",
                        "ConsumerTests.test_rofi_native_theme_parser",
                        "ConsumerTests.test_all_svg_assets_render_with_librsvg",
                    ],
                    [
                        str(tests / "test_readability.py"),
                        "ReadabilityTests.test_alacritty_text_cursor_selection_and_faint_palette",
                        "ReadabilityTests.test_kitty_text_tabs_selection_and_faint_palette",
                        "ReadabilityTests.test_bat_syntax_over_normal_line_and_selection_backgrounds",
                        "ReadabilityTests.test_openbox_enabled_labels_and_actionable_buttons",
                        "ReadabilityTests.test_zsh_completion_pairs_use_terminal_palette",
                    ],
                ]
            elif args.group == "cinnamon":
                commands = [
                    [str(tests / "cinnamon_colors.py"), str(root), str(evidence)]
                ]
            else:
                commands = [
                    [
                        str(
                            tests
                            / (
                                "test_shell46.py"
                                if args.group == "shell46"
                                else "test_shell.py"
                            )
                        ),
                        (
                            "Shell46Tests"
                            if args.group == "shell46"
                            else "ShellRuntimeTests"
                        ),
                    ]
                ]
                if args.group == "shell46":
                    commands.append(
                        [
                            str(tests / "shell46_assets.py"),
                            str(root),
                            str(evidence / "focus-rings"),
                        ]
                    )
            for index, command in enumerate(commands):
                env = dict(
                    os.environ,
                    THEME_TEST_OUTPUT=str(evidence),
                    PYTHONDONTWRITEBYTECODE="1",
                )
                if args.group == "shell51":
                    preset = json.loads((ROOT / "palette/accents.json").read_text())[
                        "presets"
                    ][color]["colors"]
                    env["THEME_TEST_FIXED_ACCENT_FILL"] = preset["accent_fill"]
                with (evidence / f"command-{index}.log").open("w") as log:
                    invocation = [sys.executable, *command]
                    if args.group == "cinnamon":
                        # A separate display and bus prevent a previous session's
                        # autostart processes/name owners affecting the next color.
                        invocation = [
                            "xvfb-run",
                            "-a",
                            "-s",
                            "-screen 0 1600x1200x24 +extension GLX +render -noreset",
                            "dbus-run-session",
                            "--",
                            *invocation,
                        ]
                    result = subprocess.run(
                        invocation,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        timeout=240,
                    )
                results.append(
                    {
                        "color": color,
                        "command": command[0].split("/")[-1],
                        "args": command[1:],
                        "status": result.returncode,
                    }
                )
                (output / "results.json").write_text(
                    json.dumps(results, indent=2) + "\n"
                )
                print(
                    f"{color} {args.group} {index + 1}/{len(commands)}: {result.returncode}",
                    flush=True,
                )
                if result.returncode:
                    print((evidence / f"command-{index}.log").read_text(), flush=True)
                    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
