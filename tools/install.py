#!/usr/bin/env python3
"""Install committed theme files and reversible, explicitly selected configuration."""
import sys

if sys.version_info < (3, 11):
    sys.exit("Python 3.11 or newer is required.")
import argparse
import base64
import copy
import ctypes
import ctypes.util
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import tomllib
import uuid
import pwd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flatpak_support as sandbox

THEME = "Adwaita-AMOLED"
ROOT = Path(__file__).resolve().parents[1]
DIRS = {
    "cinnamon",
    "gnome-shell",
    "gtk-2.0",
    "gtk-3.0",
    "gtk-4.0",
    "metacity-1",
    "openbox-3",
    "extra",
    "tools",
}
FILES = {
    "index.theme",
    "LICENSE",
    "README.md",
    "INSTALLING.md",
    "COMPATIBILITY.md",
    "COLOR_READABILITY.md",
    "COLOR_COMPLETENESS.md",
    "install.sh",
}
COMPONENTS = {
    "gtk": "Install the GTK theme; desktop selection uses --activate.",
    "libadwaita": "Manage one import in the native GTK4 user stylesheet.",
    "qt": "Install Qt5ct/Qt6ct palettes and optional scrollbar QSS; select them in Qt settings.",
    "kitty": "Add a managed include to kitty.conf (colors, cursor and tab settings).",
    "alacritty": "Add a managed TOML import; local color settings still take precedence.",
    "bat": "Install/activate the syntax palette and build its theme cache.",
    "nvim": "Install/activate the Neovim and Airline themes in the selected profile.",
    "rofi": "Add a managed theme import to config.rasi.",
    "zsh": "Source the prompt/completion/highlighting snippet after existing configuration.",
    "wallpaper": "Copy the supplied wallpaper into the user backgrounds directory.",
    "shell": "Install the matching GNOME Shell 46/51 theme; optional User Themes activation.",
}


class InstallError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args, env=None):
    try:
        result = subprocess.run(
            args, text=True, capture_output=True, timeout=60, env=env
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InstallError(f"Cannot run {args[0]}: {error}") from error
    if result.returncode:
        raise InstallError(
            f"{args[0]} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def location(value, label):
    p = Path(value).expanduser()
    if not p.is_absolute() or p == Path("/") or any(c in str(p) for c in "\n\r\0"):
        raise InstallError(
            f"{label} must be an absolute directory other than /, without newlines."
        )
    return p.resolve()


def roots():
    home = location(os.environ.get("HOME", str(Path.home())), "HOME")
    return {
        "home": home,
        "data": location(
            os.environ.get("XDG_DATA_HOME") or str(home / ".local/share"),
            "XDG_DATA_HOME",
        ),
        "config": location(
            os.environ.get("XDG_CONFIG_HOME") or str(home / ".config"),
            "XDG_CONFIG_HOME",
        ),
        "cache": location(
            os.environ.get("XDG_CACHE_HOME") or str(home / ".cache"), "XDG_CACHE_HOME"
        ),
        "state": location(
            os.environ.get("XDG_STATE_HOME") or str(home / ".local/state"),
            "XDG_STATE_HOME",
        ),
    }


def summary(snap):
    return {k: v for k, v in snap.items() if k != "data"}


def snapshot(path, ownership=False):
    owner = (
        {"uid": path.lstat().st_uid, "gid": path.lstat().st_gid}
        if ownership and os.path.lexists(path)
        else {}
    )
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path), **owner}
    if not path.exists():
        return {"kind": "absent"}
    if path.is_dir():
        return {"kind": "directory", "mode": stat.S_IMODE(path.stat().st_mode), **owner}
    if not path.is_file():
        raise InstallError(f"Expected a regular file: {path}")
    data = path.read_bytes()
    return {
        "kind": "file",
        "sha256": digest(data),
        "mode": stat.S_IMODE(path.stat().st_mode),
        "data": base64.b64encode(data).decode("ascii"),
        **owner,
    }


def desired(data, mode=0o644):
    return {"kind": "file", "sha256": digest(data), "mode": mode}


def guard(path, directories):
    # Resolve the XDG roots once, then reject redirected descendants.
    candidates = [p for p in directories if path.is_relative_to(p)]
    if not candidates:
        raise InstallError(
            f"Destination is outside the selected user directories: {path}"
        )
    base = max(candidates, key=lambda p: len(p.parts))
    for part in [path.parent, *path.parent.parents]:
        if part.is_symlink():
            raise InstallError(
                f"Directory is a symlink; use its real XDG location or configure this component manually: {part}"
            )
        if part == base:
            break


def atomic(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".amoled-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def restore(path, snap):
    if snap["kind"] == "absent":
        if os.path.lexists(path):
            path.rmdir() if path.is_dir() and not path.is_symlink() else path.unlink()
    elif snap["kind"] == "file":
        atomic(path, base64.b64decode(snap["data"]), snap["mode"])
    elif snap["kind"] == "directory":
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(snap["mode"])
    elif snap["kind"] == "symlink":
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.parent / (".amoled-link-" + uuid.uuid4().hex)
        try:
            temporary.symlink_to(snap["target"])
            os.replace(temporary, path)
        finally:
            if temporary.is_symlink():
                temporary.unlink()
    else:
        raise InstallError("Unsupported snapshot type.")
    if snap.get("uid") is not None:
        os.chown(path, snap["uid"], snap["gid"], follow_symlinks=False)


def read_text(path):
    try:
        return path.read_bytes().decode("utf-8") if path.exists() else ""
    except (UnicodeError, OSError) as error:
        raise InstallError(
            f"Cannot read UTF-8 configuration {path}: {error}"
        ) from error


def remove_fragments(text, fragments, updating=False):
    for item in fragments:
        block = item["block"]
        if text.count(block) != 1:
            raise InstallError(
                "A managed configuration block was changed or removed; preserve/resolve that edit before updating or undoing."
            )
        replacement = (
            item.get("update_restore", item["restore"]) if updating else item["restore"]
        )
        text = text.replace(block, replacement, 1)
    return text


def block(body, language="hash"):
    begin, end = {
        "hash": ("# BEGIN Adwaita-AMOLED", "# END Adwaita-AMOLED"),
        "css": ("/* BEGIN Adwaita-AMOLED */", "/* END Adwaita-AMOLED */"),
        "lua": ("-- BEGIN Adwaita-AMOLED", "-- END Adwaita-AMOLED"),
        "vim": ('" BEGIN Adwaita-AMOLED', '" END Adwaita-AMOLED'),
    }[language]
    return begin + "\n" + body.rstrip("\n") + "\n" + end + "\n"


def append_fragment(text, body, language="hash"):
    inserted = ("" if not text or text.endswith("\n") else "\n") + block(body, language)
    return text + inserted, [{"block": inserted, "restore": ""}]


def gtk_version():
    try:
        library = ctypes.CDLL(ctypes.util.find_library("gtk-4") or "libgtk-4.so.1")
        return tuple(
            getattr(library, "gtk_get_" + part + "_version")()
            for part in ("major", "minor", "micro")
        )
    except (OSError, AttributeError):
        return None


def gsettings_command(spec):
    args = ["gsettings"]
    if spec.get("schema_dir"):
        args += ["--schemadir", spec["schema_dir"]]
    return args


def setting_get(spec):
    if spec["backend"] == "gsettings":
        # GVariant annotates an empty string array as @as []; normalize it so
        # planned values compare with the canonical value returned after writes.
        return command(
            gsettings_command(spec) + ["get", spec["schema"], spec["key"]]
        ).removeprefix("@as ")
    return command(["xfconf-query", "-c", spec["schema"], "-p", spec["key"]])


def setting_set(spec, value):
    if spec["backend"] == "gsettings":
        command(gsettings_command(spec) + ["set", spec["schema"], spec["key"], value])
    else:
        command(["xfconf-query", "-c", spec["schema"], "-p", spec["key"], "-s", value])


class Plan:
    def __init__(self, directories, state, system=False):
        self.roots, self.state, self.system = directories, state, system
        self.directory_roots = []
        self.allowed = list(directories.values())
        self.operations, self.messages, self.settings = {}, [], []
        self.bat = None
        self.forget_files, self.forget_settings = set(), set()

    def ensure_parents(self, path):
        if not self.system:
            return
        parents = []
        for parent in [path.parent, *path.parent.parents]:
            guard(parent / ".directory", self.allowed)
            adopted = any(parent.is_relative_to(base) for base in self.directory_roots)
            if parent.exists() and not adopted:
                boundary = self.roots["system_root"]
                for ancestor in [parent, *parent.parents]:
                    if not ancestor.is_relative_to(boundary):
                        break
                    info = ancestor.lstat()
                    if (
                        ancestor.is_symlink()
                        or info.st_uid != 0
                        or stat.S_IMODE(info.st_mode) & 0o022
                    ):
                        raise InstallError(
                            f"System destination ancestors must be root-owned and protected from other writers: {ancestor}"
                        )
                    if ancestor == boundary:
                        break
                break
            parents.append(parent)
        for parent in reversed(parents):
            before = snapshot(parent, True)
            if before["kind"] not in ["absent", "directory"]:
                raise InstallError(
                    f"System directory must be a real directory: {parent}"
                )
            after = {"kind": "directory", "mode": 0o755, "uid": 0, "gid": 0}
            self.operations[str(parent)] = {
                "path": parent,
                "after": after,
                "component": "system-directory",
                "ownership": True,
                "expected_before": summary(before),
            }

    def put(self, path, data, component, fragments=None, mode=None, metadata=None):
        guard(path, self.allowed)
        self.ensure_parents(path)
        before = snapshot(path, self.system)
        if before["kind"] == "directory":
            raise InstallError(f"Expected a regular file: {path}")
        previous = self.state.get("files", {}).get(str(path))
        if (
            previous
            and not fragments
            and metadata is None
            and summary(before) != previous["after"]
        ):
            if before.get("sha256") != digest(data):
                raise InstallError(
                    f"Installed file has local edits; keeping it unchanged: {path}"
                )
        if mode is None:
            mode = before.get("mode", 0o644)
        self.operations[str(path)] = {
            "path": path,
            "data": data,
            "mode": mode,
            "component": component,
            "after": dict(
                desired(data, mode), **({"uid": 0, "gid": 0} if self.system else {})
            ),
            "fragments": fragments,
            "ownership": self.system,
            "metadata": metadata,
            "expected_before": summary(before),
        }

    def base_text(self, path):
        guard(path, self.allowed)
        text = read_text(path)
        previous = self.state.get("files", {}).get(str(path), {})
        if previous.get("fragments"):
            text = remove_fragments(text, previous["fragments"], updating=True)
        elif "BEGIN Adwaita-AMOLED" in text:
            raise InstallError(
                f"Found an installer marker without its saved state: {path}"
            )
        return text

    def append(self, path, body, component, language="hash"):
        text = self.base_text(path)
        updated, fragments = append_fragment(text, body, language)
        self.put(path, updated.encode(), component, fragments)

    def add_setting(self, backend, schema, key, value, component, schema_dir=None):
        spec = {
            "backend": backend,
            "schema": schema,
            "key": key,
            "component": component,
        }
        if schema_dir:
            spec["schema_dir"] = str(schema_dir)
        spec["before"] = setting_get(spec)
        spec["after"] = repr(value) if backend == "gsettings" else value
        identity = backend + ":" + schema + ":" + key
        old = self.state.get("settings", {}).get(identity)
        if old and spec["before"] not in [old["after"], spec["after"]]:
            raise InstallError(
                f"Desktop preference changed since installation: {schema} {key}"
            )
        spec["id"] = identity
        self.settings.append(spec)

    def show(self):
        changed = 0
        for item in self.operations.values():
            if (
                summary(snapshot(item["path"], item.get("ownership", False)))
                != item["after"]
            ):
                print(f"  [{item['component']}] {item['path']}")
                changed += 1
        for spec in self.settings:
            print(
                f"  [{spec['component']}] {spec['schema']} / {spec['key']} -> {spec['after']}"
            )
        print(
            f"{changed} path(s) to write; {len(self.settings)} desktop preference(s)."
        )
        for message in self.messages:
            print("  Note: " + message)


class Store:
    def __init__(self, directories):
        self.roots = directories
        self.directory = directories["state"] / "adwaita-amoled"
        self.file = self.directory / "state.json"
        self.pending = self.directory / "pending.json"
        guard(self.file, list(directories.values()))
        if "system_root" in directories:
            for path in [
                self.directory,
                self.file,
                self.pending,
                self.directory / "lock",
                self.directory / "backups",
            ]:
                if os.path.lexists(path):
                    info = path.lstat()
                    if (
                        path.is_symlink()
                        or info.st_uid != 0
                        or stat.S_IMODE(info.st_mode) & 0o022
                    ):
                        raise InstallError(
                            f"System installer state must be root-owned, without symlinks or group/other write access: {path}"
                        )
        self.state = {"version": 2, "files": {}, "settings": {}, "options": {}}
        if self.file.exists():
            try:
                self.state = json.loads(self.file.read_text())
                if not isinstance(self.state, dict) or self.state.get(
                    "version"
                ) not in [1, 2]:
                    raise ValueError("unsupported state version")
                if any(
                    not isinstance(self.state.get(key), dict)
                    for key in ["files", "settings", "options"]
                ):
                    raise ValueError("invalid installer state structure")
            except (ValueError, KeyError) as error:
                raise InstallError(f"Cannot read installer state: {error}") from error

    def save(self):
        atomic(self.file, (json.dumps(self.state, indent=2) + "\n").encode())

    def recover(self):
        if not self.pending.exists():
            return
        journal = json.loads(self.pending.read_text())
        problems = []
        for entry in reversed(journal["changes"]):
            try:
                if entry["kind"] == "file":
                    path = Path(entry["path"])
                    guard(
                        path,
                        [
                            location(p, "saved directory")
                            for p in journal.get("allowed", [])
                        ]
                        + list(self.roots.values()),
                    )
                    actual = summary(
                        snapshot(path, entry["after"].get("uid") is not None)
                    )
                    if actual not in [summary(entry["before"]), entry["after"]]:
                        raise InstallError(f"Changed after interruption: {path}")
                    restore(path, entry["before"])
                else:
                    actual = setting_get(entry["spec"])
                    if actual not in [entry["before"], entry["after"]]:
                        raise InstallError(
                            "Desktop setting changed after interruption."
                        )
                    setting_set(entry["spec"], entry["before"])
            except (InstallError, OSError) as error:
                problems.append(str(error))
        if problems:
            raise InstallError(
                "Recovery kept conflicting user changes: " + "; ".join(problems)
            )
        self.state = journal["previous_state"]
        self.save()
        self.pending.unlink()
        print(
            "Recovered the interrupted installation; previous files/preferences restored."
        )

    def transact(self, plan, options=None, uninstall=False):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        backups = self.directory / "backups"
        guard(backups / "transaction.json", list(self.roots.values()))
        backups.mkdir(exist_ok=True, mode=0o700)
        journal = {
            "previous_state": copy.deepcopy(self.state),
            "changes": [],
            "allowed": [str(p) for p in plan.allowed],
        }

        def journal_save():
            atomic(self.pending, (json.dumps(journal, indent=2) + "\n").encode())

        def write(item):
            path = item["path"]
            guard(path, plan.allowed)
            before = snapshot(path, item.get("ownership", False))
            if (
                item.get("expected_before") is not None
                and summary(before) != item["expected_before"]
            ):
                raise InstallError(f"File changed after the plan was displayed: {path}")
            after = item.get("after", {"kind": "absent"})
            if summary(before) != after:
                journal["changes"].append(
                    {
                        "kind": "file",
                        "path": str(path),
                        "before": before,
                        "after": after,
                    }
                )
                journal_save()
                if "restore" in item:
                    restore(path, item["restore"])
                elif after["kind"] == "directory":
                    restore(path, after)
                else:
                    atomic(path, item["data"], item["mode"])
                    if item.get("ownership"):
                        os.chown(path, after["uid"], after["gid"])
            if uninstall:
                self.state["files"].pop(str(path), None)
            else:
                origin = self.state["files"].get(str(path), {}).get("before", before)
                old = self.state["files"].get(str(path), {})
                edited = old.get("external_edits", False) or (
                    (
                        bool(old.get("fragments"))
                        or bool((old.get("metadata") or {}).get("flatpak"))
                    )
                    and summary(before) != old.get("after")
                )
                self.state["files"][str(path)] = {
                    "before": origin,
                    "after": after,
                    "component": item["component"],
                    "fragments": item.get("fragments"),
                    "external_edits": edited,
                    "ownership": item.get("ownership", False),
                    "metadata": item.get("metadata"),
                }

        journal_save()
        try:
            for item in plan.operations.values():
                write(item)
            if plan.bat:
                executable, cache = plan.bat
                with tempfile.TemporaryDirectory(prefix="amoled-bat-") as temporary:
                    env = dict(os.environ, BAT_CACHE_PATH=temporary)
                    command([executable, "cache", "--build"], env=env)
                    staged = sorted(
                        p for p in Path(temporary).rglob("*") if p.is_file()
                    )
                    if not staged:
                        raise InstallError("bat did not produce its theme cache.")
                    for path in staged:
                        target = cache / path.relative_to(temporary)
                        guard(target, plan.allowed)
                        write(
                            {
                                "path": target,
                                "data": path.read_bytes(),
                                "mode": 0o644,
                                "component": "bat-cache",
                                "after": desired(path.read_bytes()),
                            }
                        )
            for spec in plan.settings:
                before = setting_get(spec)
                if before != spec["before"]:
                    raise InstallError(
                        "Desktop preference changed after planning: " + spec["id"]
                    )
                journal["changes"].append(
                    {
                        "kind": "setting",
                        "spec": spec,
                        "before": before,
                        "after": spec["after"],
                    }
                )
                journal_save()
                setting_set(spec, spec["after"])
                if uninstall:
                    self.state["settings"].pop(spec["id"], None)
                else:
                    origin = (
                        self.state["settings"].get(spec["id"], {}).get("before", before)
                    )
                    record = dict(spec, before=origin)
                    old = self.state["settings"].get(spec["id"], {})
                    for key in ["list_added", "list_removed"]:
                        if key in old:
                            record[key] = old[key]
                    self.state["settings"][spec["id"]] = record
            for name in plan.forget_files:
                self.state["files"].pop(name, None)
            for name in plan.forget_settings:
                self.state["settings"].pop(name, None)
            if options is not None:
                self.state["options"] = options
            if uninstall and not self.state["files"] and not self.state["settings"]:
                self.state["options"] = {}
            self.state["version"] = 2
            self.save()
            backup = backups / (
                datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                + "-"
                + uuid.uuid4().hex[:8]
                + ".json"
            )
            atomic(backup, (json.dumps(journal, indent=2) + "\n").encode())
            self.pending.unlink()
            print(f"Backup and transaction record: {backup}")
        except BaseException:
            self.recover()
            raise


def components(value):
    selected = (
        set(COMPONENTS)
        if value.strip() == "all"
        else {part.strip() for part in value.split(",") if part.strip()}
    )
    unknown = selected - COMPONENTS.keys()
    if unknown:
        raise InstallError("Unknown components: " + ", ".join(sorted(unknown)))
    return selected


def shell_variant(requested="auto", required=False):
    if requested != "auto":
        return requested
    if shutil.which("gnome-shell"):
        version = command(["gnome-shell", "--version"])
        match = re.search(r"\b(\d+)\.", version)
        if match and match[1] in {"46", "51"}:
            return match[1]
        if required:
            raise InstallError(
                f"Unsupported Shell version: {version}. Bundled variants target 46.x and 51.x."
            )
    elif required:
        raise InstallError(
            "Cannot detect GNOME Shell. Use --shell-version 46 or 51 after checking the target desktop."
        )
    return "51"


def runtime(plan, target, shell_version="51"):
    legacy = plan.roots["home"] / ".themes" / THEME
    if not plan.system and legacy.exists() and legacy.resolve() != target.resolve():
        raise InstallError(
            f"An older theme directory can shadow the new installation: {legacy}. Move it outside ~/.themes (keep it as a backup), then rerun setup. No theme files were changed."
        )
    if target != ROOT and (ROOT.is_relative_to(target) or target.is_relative_to(ROOT)):
        raise InstallError(
            "The checkout is inside the installation destination; move it elsewhere first."
        )
    required = [
        "index.theme",
        "gtk-3.0/gtk.gresource",
        "gtk-4.0/gtk.gresource",
        "extra/libadwaita/gtk.css",
        "tools/install.py",
        "tools/flatpak_support.py",
        "tools/legacy-gtk4.json",
        "install.sh",
        "gnome-shell/gnome-shell-46.css",
        "gnome-shell/gnome-shell-51.css",
    ]
    if plan.system:
        plan.directory_roots.append(target)
    for name in required:
        if not (ROOT / name).is_file():
            raise InstallError("Incomplete theme package: missing " + name)
    for path in sorted(ROOT.rglob("*")):
        name = path.relative_to(ROOT)
        if name.parts[0] not in DIRS and str(name) not in FILES:
            continue
        if "__pycache__" in name.parts or not path.is_file():
            continue
        if path.is_symlink():
            raise InstallError(f"Unexpected link in the theme package: {name}")
        if path == target / name and name != Path("gnome-shell/gnome-shell.css"):
            continue
        mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
        data = path.read_bytes()
        if name == Path("gnome-shell/gnome-shell.css"):
            data = (ROOT / f"gnome-shell/gnome-shell-{shell_version}.css").read_bytes()
        plan.put(target / name, data, "theme", mode=mode)
    plan.messages.append(
        f"GTK2 requires Murrine from your distribution. Theme destination: {target}"
    )
    plan.messages.append(
        f"Bundled Shell stylesheet selected: GNOME {shell_version}. Auto selection supports 46.x and 51.x; other major versions are unverified."
    )


def libadwaita(plan, target, mode, path=None, component="libadwaita"):
    version = gtk_version()
    if mode == "auto":
        if version is None:
            raise InstallError(
                "Cannot detect native GTK4. Choose --gtk4-mode legacy or modern explicitly, or omit libadwaita."
            )
        mode = "modern" if version >= (4, 16, 0) else "legacy"
    entry = (
        target
        / "extra/libadwaita"
        / ("gtk-modern.css" if mode == "modern" else "gtk.css")
    )
    path = path or plan.roots["config"] / "gtk-4.0/gtk.css"
    text = plan.base_text(path)
    fingerprints = json.loads((ROOT / "tools/legacy-gtk4.json").read_text())
    originals = [
        ROOT / "extra/libadwaita" / name
        for name in ["gtk.css", "gtk-dark.css", "gtk-modern.css"]
    ]
    fingerprints.update({digest(p.read_bytes()): str(p) for p in originals})
    old = plan.state.get("files", {}).get(str(path), {}).get("fragments") or []
    original = old[0]["restore"] if old else ""
    if digest(text.encode()) in fingerprints:
        original, text = text, ""
        plan.messages.append(
            "Recognized a complete earlier theme override; it will be backed up and replaced by the import."
        )
    added = block("@import url(" + json.dumps(entry.as_uri()) + ");", "css")
    # @charset, if present, must remain the first statement.
    charset = re.match(r'\A\s*@charset\s+["\'][^"\']+["\']\s*;[^\n]*(?:\n|$)', text)
    offset = charset.end() if charset else 0
    updated = text[:offset] + added + text[offset:]
    fragments = [{"block": added, "restore": original, "update_restore": ""}]
    plan.put(path, updated.encode(), component, fragments)
    plan.messages.append(
        f"{component} GTK4 override: {mode}; restart applications after installing/updating. Existing custom CSS remains and can override the palette."
    )
    if component == "libadwaita":
        plan.messages.append(
            "This import configures native GTK4. Flatpak apps use their own --flatpak option."
        )


def config_dirs():
    return [
        Path(p)
        for p in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":")
        if Path(p).is_absolute()
    ]


def alacritty_config(plan):
    config, home = plan.roots["config"], plan.roots["home"]
    # Match Alacritty 0.15's installed_config search, including shared XDG paths.
    bases = [config, *config_dirs()]
    candidates = [p / "alacritty/alacritty.toml" for p in bases]
    candidates += [p / "alacritty.toml" for p in bases]
    candidates += [home / ".config/alacritty/alacritty.toml", home / ".alacritty.toml"]
    selected = next((p for p in candidates if p.exists() or p.is_symlink()), None)
    if selected:
        if not any(selected.is_relative_to(p) for p in [config, home]):
            raise InstallError(
                f"Alacritty is loading a shared config: {selected}. Create a user config importing it, or add the theme import manually; setup will not replace shared configuration."
            )
        return selected
    for candidate in candidates:
        for suffix in [".yml", ".yaml"]:
            if candidate.with_suffix(suffix).exists():
                raise InstallError(
                    "Migrate the existing Alacritty YAML configuration to current TOML before selecting alacritty."
                )
    return candidates[0]


def kitty_config(plan):
    custom = os.environ.get("KITTY_CONFIG_DIRECTORY")
    if custom:
        directory = location(custom, "KITTY_CONFIG_DIRECTORY")
        plan.allowed.append(directory)
        return directory / "kitty.conf"
    candidates = [
        plan.roots["config"] / "kitty/kitty.conf",
        plan.roots["home"] / ".config/kitty/kitty.conf",
    ]
    selected = next((p for p in candidates if p.exists() or p.is_symlink()), None)
    if selected:
        return selected
    for directory in config_dirs():
        shared = directory / "kitty/kitty.conf"
        if shared.exists() and shared != Path("/etc/xdg/kitty/kitty.conf"):
            raise InstallError(
                f"Kitty is loading a shared config: {shared}. Choose KITTY_CONFIG_DIRECTORY explicitly or add the theme include manually."
            )
    return candidates[0]


def alacritty(plan, target):
    path = alacritty_config(plan)
    text = plan.base_text(path)
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise InstallError(f"Invalid Alacritty TOML: {error}") from error
    if "import" in data:
        raise InstallError(
            "Migrate the old top-level Alacritty import to [general] first; the installer supports current TOML configuration."
        )
    general = data.get("general", {})
    if (
        not isinstance(general, dict)
        or not isinstance(general.get("import", []), list)
        or not all(isinstance(p, str) for p in general.get("import", []))
    ):
        raise InstallError("Alacritty general.import must be a list of paths.")
    imports = general.get("import", []).copy()
    name = str(target / "extra/alacritty/alacritty.toml")
    if name not in imports:
        imports.append(name)
    body = "import = " + json.dumps(imports, ensure_ascii=False)
    headers = list(
        re.finditer(r"(?m)^[ \t]*\[general\][ \t]*(?:#[^\r\n]*)?\r?(?:\n|$)", text)
    )
    if len(headers) > 1 or ("general" in data and not headers):
        raise InstallError(
            "This Alacritty inline/dotted general table needs a manual import; no files were changed."
        )
    if not headers:
        updated, fragments = append_fragment(text, "[general]\n" + body)
    else:
        start = headers[0].end()
        tail = text[start:]
        next_table = re.search(r"(?m)^[ \t]*\[[^\n]+\][ \t]*(?:#[^\n]*)?$", tail)
        end = start + next_table.start() if next_table else len(text)
        matches = list(re.finditer(r"(?m)^[ \t]*import[ \t]*=", text[start:end]))
        original = ""
        stop = start
        if "import" in general:
            if len(matches) != 1:
                raise InstallError(
                    "Cannot safely identify the Alacritty import assignment."
                )
            begin = start + matches[0].start()
            value_start = start + matches[0].end()
            for stop in [
                m.end()
                for m in re.finditer(r".*(?:\n|$)", text[value_start:end])
                if m.end() > 0
            ]:
                stop += value_start
                try:
                    parsed = tomllib.loads("value=" + text[value_start:stop])
                    if parsed.get("value") == general["import"]:
                        break
                except tomllib.TOMLDecodeError:
                    continue
            else:
                raise InstallError("Cannot safely read the Alacritty import list.")
            original = text[begin:stop]
            start = begin
        inserted = block(body)
        updated = text[:start] + inserted + text[stop:]
        fragments = [{"block": inserted, "restore": original}]
    expected = copy.deepcopy(data)
    expected.setdefault("general", {})["import"] = imports
    try:
        if tomllib.loads(updated) != expected:
            raise ValueError("other settings would change")
    except (tomllib.TOMLDecodeError, ValueError) as error:
        raise InstallError(
            f"Cannot safely update the Alacritty import: {error}"
        ) from error
    plan.put(path, updated.encode(), "alacritty", fragments)
    plan.messages.append(
        "Alacritty: current TOML layout (0.15 tested); local [colors] settings take precedence over imports."
    )


def extras(plan, target, selected):
    config, home, data = (plan.roots[x] for x in ["config", "home", "data"])
    if "qt" in selected:
        for qt in ["qt5ct", "qt6ct"]:
            for sub in [
                "colors/Adwaita-AMOLED.conf",
                "qss/fusion-simple-scrollbar.qss",
            ]:
                plan.put(
                    config / qt / sub, (ROOT / "extra" / qt / sub).read_bytes(), "qt"
                )
        plan.messages.append(
            "Qt: select Adwaita-AMOLED in qt5ct/qt6ct. Install/select the matching platform plugin per Qt version; no global QT_QPA_PLATFORMTHEME is set."
        )
    if "kitty" in selected:
        plan.append(
            kitty_config(plan),
            "include " + str(target / "extra/kitty/adwaita-amoled.conf"),
            "kitty",
        )
    if "alacritty" in selected:
        alacritty(plan, target)
    if "nvim" in selected:
        profile = os.environ.get("NVIM_APPNAME") or "nvim"
        if profile in [".", ".."] or "/" in profile or "\\" in profile:
            raise InstallError("NVIM_APPNAME must be a single profile directory name.")
        directory = config / profile
        for sub, src in [
            ("colors/adwaita-amoled.vim", "colors/adwaita-amoled.vim"),
            (
                "autoload/airline/themes/adwaita_amoled.vim",
                "autoload/airline/themes/adwaita_amoled.vim",
            ),
        ]:
            plan.put(directory / sub, (ROOT / "extra/nvim" / src).read_bytes(), "nvim")
        lua, vim = directory / "init.lua", directory / "init.vim"
        if lua.exists() and vim.exists():
            raise InstallError(
                "Both init.lua and init.vim exist; resolve the active Neovim configuration first."
            )
        if vim.exists():
            plan.append(
                vim,
                "set termguicolors\ncolorscheme adwaita-amoled\nlet g:airline_theme = 'adwaita_amoled'",
                "nvim",
                "vim",
            )
        else:
            plan.append(
                lua,
                'vim.opt.termguicolors = true\nvim.cmd("colorscheme adwaita-amoled")\nvim.g.airline_theme = "adwaita_amoled"',
                "nvim",
                "lua",
            )
    if "rofi" in selected:
        # Rasi accepts quoted absolute paths, with C-style escaping for quotes.
        plan.append(
            config / "rofi/config.rasi",
            "@import "
            + json.dumps(
                str(target / "extra/rofi/adwaita-dark.rasi"), ensure_ascii=False
            ),
            "rofi",
            "css",
        )
    if "zsh" in selected:
        zdot = location(os.environ.get("ZDOTDIR") or str(home), "ZDOTDIR")
        plan.allowed.append(zdot)
        plan.append(
            zdot / ".zshrc",
            "source " + shlex.quote(str(target / "extra/zsh/.zshrc")),
            "zsh",
        )
        plan.messages.append(
            "Zsh: changes prompt, completion styles, title hook and optional plugin colors; load highlighting plugins before the managed block."
        )
    if "wallpaper" in selected:
        dest = data / "backgrounds/Adwaita-AMOLED/blackmount.png"
        plan.put(
            dest, (ROOT / "extra/wallpaper/blackmount.png").read_bytes(), "wallpaper"
        )
        plan.messages.append(
            f"Wallpaper copied to {dest}; choose it in desktop background settings."
        )
    if "bat" in selected:
        executable = shutil.which("bat") or shutil.which("batcat")
        if not executable:
            raise InstallError(
                "Install bat/batcat before selecting bat (needed to build and verify its cache)."
            )
        directory = location(
            command([executable, "--config-dir"]), "bat configuration directory"
        )
        cache = location(command([executable, "--cache-dir"]), "bat cache directory")
        configfile = (
            location(os.environ["BAT_CONFIG_PATH"], "BAT_CONFIG_PATH")
            if os.environ.get("BAT_CONFIG_PATH")
            else directory / "config"
        )
        plan.allowed.extend([directory, cache, configfile.parent])
        plan.put(
            directory / "themes/adwaita-amoled.tmTheme",
            (ROOT / "extra/bat/themes/adwaita-amoled.tmTheme").read_bytes(),
            "bat",
        )
        plan.append(configfile, '--theme="adwaita-amoled"', "bat")
        plan.bat = (executable, cache)
        plan.messages.append(
            f"bat cache will be rebuilt in a temporary directory, then backed up/installed into {cache}."
        )


def activation(plan, selected, enabled, desktop):
    if not enabled:
        plan.messages.append(
            "Desktop selection is unchanged. Use appearance settings or --activate to select the installed theme."
        )
        return
    if "gtk" in selected:
        name = desktop.upper()
        if "CINNAMON" in name:
            plan.add_setting(
                "gsettings", "org.cinnamon.desktop.interface", "gtk-theme", THEME, "gtk"
            )
            plan.add_setting(
                "gsettings",
                "org.cinnamon.desktop.wm.preferences",
                "theme",
                THEME,
                "gtk",
            )
            plan.add_setting("gsettings", "org.cinnamon.theme", "name", THEME, "gtk")
        elif "MATE" in name:
            plan.add_setting(
                "gsettings", "org.mate.interface", "gtk-theme", THEME, "gtk"
            )
            plan.add_setting(
                "gsettings", "org.mate.Marco.general", "theme", THEME, "gtk"
            )
        elif "XFCE" in name:
            plan.add_setting("xfconf", "xsettings", "/Net/ThemeName", THEME, "gtk")
            plan.messages.append(
                "No Xfwm4 decoration theme is provided; its existing theme is retained."
            )
        elif "GNOME" in name or "BUDGIE" in name:
            plan.add_setting(
                "gsettings", "org.gnome.desktop.interface", "gtk-theme", THEME, "gtk"
            )
        else:
            raise InstallError(
                "Cannot identify the desktop for activation. Set XDG_CURRENT_DESKTOP correctly or omit --activate."
            )
    if "shell" in selected:
        if "GNOME" not in desktop.upper():
            raise InstallError("Shell activation is only supported inside GNOME Shell.")
        version = command(["gnome-shell", "--version"])
        if not re.search(r"\b(?:46|51)\.", version):
            raise InstallError(
                "The bundled Shell theme supports GNOME Shell 46.x and 51.x only."
            )
        extension = "user-theme@gnome-shell-extensions.gcampax.github.com"
        if extension not in command(["gnome-extensions", "list"]).splitlines():
            raise InstallError(
                "Install the GNOME User Themes extension first, then log in again and rerun setup."
            )
        if (
            command(["gsettings", "get", "org.gnome.shell", "disable-user-extensions"])
            == "true"
        ):
            raise InstallError(
                "User extensions are globally disabled. Enable them in Extensions first; setup will not enable unrelated extensions."
            )
        schema_dir = None
        schema = "org.gnome.shell.extensions.user-theme"
        if schema not in command(["gsettings", "list-schemas"]).splitlines():
            bases = [plan.roots["data"]] + [
                Path(p)
                for p in os.environ.get(
                    "XDG_DATA_DIRS", "/usr/local/share:/usr/share"
                ).split(":")
                if p
            ]
            schema_dir = next(
                (
                    base / "gnome-shell/extensions" / extension / "schemas"
                    for base in bases
                    if (
                        base
                        / "gnome-shell/extensions"
                        / extension
                        / "schemas/gschemas.compiled"
                    ).is_file()
                ),
                None,
            )
            if schema_dir is None:
                raise InstallError(
                    "The User Themes settings schema is unavailable. Reinstall the extension and log in again."
                )
        plan.add_setting(
            "gsettings", schema, "name", THEME, "shell", schema_dir=schema_dir
        )
        for key, enable in [
            ("enabled-extensions", True),
            ("disabled-extensions", False),
        ]:
            raw = setting_get(
                {"backend": "gsettings", "schema": "org.gnome.shell", "key": key}
            )
            values = string_array(raw)
            wanted = values.copy()
            if enable and extension not in wanted:
                wanted.append(extension)
            if not enable and extension in wanted:
                wanted.remove(extension)
            plan.settings.insert(
                0,
                {
                    "backend": "gsettings",
                    "schema": "org.gnome.shell",
                    "key": key,
                    "id": "gsettings:org.gnome.shell:" + key,
                    "component": "shell",
                    "before": raw,
                    "after": repr(wanted),
                    "list_added": (
                        [extension]
                        if extension not in values and extension in wanted
                        else []
                    ),
                    "list_removed": (
                        [extension]
                        if extension in values and extension not in wanted
                        else []
                    ),
                },
            )
        plan.messages.append(
            "Shell: User Themes is enabled/selected; an already loaded theme may need toggling or logging in again. GDM is unchanged."
        )


def string_array(raw):
    import ast

    try:
        values = ast.literal_eval(raw.removeprefix("@as "))
        if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
            raise ValueError("not a string array")
        return values
    except (ValueError, SyntaxError) as error:
        raise InstallError("Cannot safely read GNOME extension preferences.") from error


def undo_plan(store, system=False, flatpaks=None):
    plan = Plan(store.roots, store.state, system=system)
    entries = list(store.state.get("files", {}).items())
    entries.sort(
        key=lambda item: (
            item[1]["after"]["kind"] == "directory",
            -len(Path(item[0]).parts),
        )
    )
    for name, record in entries:
        path = Path(name)
        if flatpaks is not None:
            app = ((record.get("metadata") or {}).get("flatpak") or {}).get("app")
            app_config = record["component"] == "flatpak-css" and any(
                path.is_relative_to(
                    store.roots["home"] / ".var/app" / selected / "config"
                )
                for selected in flatpaks
            )
            if app not in flatpaks and not app_config:
                continue
        if record["component"] in [
            "zsh",
            "bat",
            "bat-cache",
            "kitty",
            "flatpak-override",
        ]:
            plan.allowed.append(path.parent)
        guard(path, plan.allowed)
        current = snapshot(path, record.get("ownership", False))
        if (
            record["after"]["kind"] == "directory"
            and record["before"]["kind"] == "absent"
        ):
            plan.forget_files.add(name)
            continue
        if record.get("metadata", {}) and record["metadata"].get("flatpak"):
            wanted = sandbox.undo_override(globals(), path, record, current)
        elif summary(current) == record["after"] and not record.get("external_edits"):
            wanted = record["before"]
        elif record.get("fragments") and current["kind"] == "file":
            text = remove_fragments(read_text(path), record["fragments"])
            data = text.encode()
            wanted = dict(
                desired(data, current["mode"]), data=base64.b64encode(data).decode()
            )
        elif record["component"] == "bat-cache":
            plan.messages.append(
                f"bat cache changed after installation; keeping it: {path}"
            )
            plan.forget_files.add(name)
            continue
        else:
            raise InstallError(
                f"Locally edited installed file will be kept: {path}. Resolve it before undo; no changes made."
            )
        plan.operations[name] = {
            "path": path,
            "restore": wanted,
            "after": summary(wanted),
            "component": record["component"],
            "expected_before": summary(current),
            "ownership": record.get("ownership", False),
        }
    for identity, old in (
        store.state.get("settings", {}).items() if flatpaks is None else []
    ):
        current = setting_get(old)
        wanted = old["before"]
        if "list_added" in old:
            values = string_array(current)
            for name in old["list_added"]:
                if name in values:
                    values.remove(name)
            for name in old["list_removed"]:
                if name not in values:
                    values.append(name)
            wanted = repr(values)
        elif current != old["after"]:
            plan.messages.append(
                "Keeping a preference changed after setup: " + identity
            )
            plan.forget_settings.add(identity)
            continue
        plan.settings.append(dict(old, id=identity, before=current, after=wanted))
    return plan


def ask(message, default=False):
    reply = input(message + (" [Y/n] " if default else " [y/N] ")).strip().lower()
    return reply in ["y", "yes"] or (not reply and default)


def system_roots(staging="/"):
    root = Path(staging).expanduser()
    if not root.is_absolute() or any(c in str(root) for c in "\n\r\0"):
        raise InstallError("--system-root must be an absolute staging directory.")
    root = root.resolve()
    home = root / pwd.getpwuid(0).pw_dir.lstrip("/")
    return {
        "system_root": root,
        "home": home,
        "data": root / "usr/local/share",
        "config": home / ".config",
        "cache": root / "var/cache",
        "state": root / "var/lib",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reversible Adwaita-AMOLED setup. System scope requires explicit --system and root; no automatic downloads."
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["install", "update", "status", "doctor", "uninstall"],
    )
    parser.add_argument(
        "--components",
        help="Comma-separated choices: " + ",".join(COMPONENTS) + "; or all",
    )
    parser.add_argument(
        "--gtk4-mode", choices=["auto", "modern", "legacy"], default=None
    )
    parser.add_argument(
        "--shell-version",
        choices=["auto", "46", "51"],
        default=None,
        help="Select the matching Shell stylesheet; auto detects the local gnome-shell version.",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Select the theme for the current supported desktop; Shell requires its component.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Apply the displayed plan without the final interactive question.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show all planned paths/settings without modifying anything.",
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Install a root-owned theme in /usr/local/share/themes, using separate system backups.",
    )
    parser.add_argument(
        "--system-root",
        default="/",
        help="Stage system paths below this directory (requires --system); normally leave as /.",
    )
    parser.add_argument(
        "--root-gtk4",
        action="store_true",
        help="With --system, also manage root user GTK4/libadwaita CSS.",
    )
    parser.add_argument(
        "--flatpak",
        action="append",
        metavar="APP_ID[=auto|modern|legacy|gtk3]",
        help="Configure a selected installed Flatpak with per-app CSS and read-only theme access; repeat for more apps.",
    )
    args = parser.parse_args(argv)
    if not args.system and (args.system_root != "/" or args.root_gtk4):
        raise InstallError("--system-root and --root-gtk4 require --system.")
    if args.system:
        if os.geteuid() != 0:
            raise InstallError(
                "System scope requires root: use sudo ./install.sh ... --system."
            )
        if (
            args.flatpak
            or args.activate
            or (args.components and components(args.components) - {"gtk", "libadwaita"})
        ):
            raise InstallError(
                "System scope installs shared theme files and optional root GTK4 CSS; run user app/Flatpak/desktop setup separately without sudo."
            )
    directories = system_roots(args.system_root) if args.system else roots()
    store = Store(directories)
    if args.action in ["status", "doctor"]:
        print(f"Installer state: {store.file}")
        print(
            f'Native GTK4: {gtk_version() or "not detected"}; desktop: {os.environ.get("XDG_CURRENT_DESKTOP") or "unknown"}'
        )
        if store.pending.exists():
            print(
                "Interrupted transaction detected; run an install/update/uninstall to recover it first."
            )
            return 1
        if not store.state["files"] and not store.state["settings"]:
            print(
                "No installation is tracked. A manually installed theme may still exist."
            )
            return 0
        differences = []
        for name, record in store.state["files"].items():
            if (
                summary(snapshot(Path(name), record.get("ownership", False)))
                != record["after"]
            ):
                differences.append(name)
        print("Components: " + ", ".join(store.state["options"].get("components", [])))
        if store.state["options"].get("shell_variant"):
            print(
                "Installed Shell stylesheet: GNOME "
                + store.state["options"]["shell_variant"]
            )
        if store.state["options"].get("flatpak"):
            print(
                "Flatpak apps: " + ", ".join(sorted(store.state["options"]["flatpak"]))
            )
        print(
            f'{len(store.state["files"])} tracked paths; {len(differences)} missing/edited files.'
        )
        for name in differences:
            print("  " + name)
        for spec in store.state["settings"].values():
            if setting_get(spec) != spec["after"]:
                differences.append(spec["id"])
                print("  Changed setting: " + spec["id"])
        print("Backups: " + str(store.directory / "backups"))
        return int(bool(differences))
    if os.environ.get("SUDO_USER") and not args.system:
        raise InstallError("Run this installer as your normal user, without sudo.")
    interactive = args.action is None and sys.stdin.isatty() and not args.system
    if args.action is None and not interactive and not args.dry_run:
        parser.print_help()
        return 2
    action = args.action or "install"
    if args.dry_run and store.pending.exists():
        raise InstallError(
            "An interrupted transaction needs recovery before a reliable dry run."
        )
    if not args.dry_run:
        store.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        lockfile = store.directory / "lock"
        if lockfile.is_symlink():
            raise InstallError("Installer lock must not be a symlink.")
        lock = lockfile.open("a")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise InstallError("Another installer is running.") from error
        # Reload after acquiring the lock, then recover incomplete transactions.
        store = Store(directories)
        store.recover()
    if action == "uninstall":
        flatpaks = (
            set(sandbox.selections(args.flatpak, {}, InstallError))
            if args.flatpak
            else None
        )
        if flatpaks is not None:
            unknown = flatpaks - store.state["options"].get("flatpak", {}).keys()
            if unknown:
                raise InstallError(
                    "No tracked Flatpak setup for: " + ", ".join(sorted(unknown))
                )
        plan = undo_plan(store, system=args.system, flatpaks=flatpaks)
        options = (
            copy.deepcopy(store.state["options"]) if flatpaks is not None else None
        )
        if options is not None:
            options["flatpak"] = {
                app: mode
                for app, mode in options.get("flatpak", {}).items()
                if app not in flatpaks
            }
    else:
        previous = store.state.get("options", {})
        selected = (
            components(args.components)
            if args.components is not None
            else set(
                previous.get("components")
                or (["gtk"] if args.system else ["gtk", "libadwaita"])
            )
        )
        selected |= set(previous.get("components", []))
        if args.root_gtk4:
            selected.add("libadwaita")
        mode = args.gtk4_mode or previous.get("gtk4_mode", "auto")
        enabled = args.activate or previous.get("activate", False)
        if interactive:
            print("Adwaita-AMOLED setup — user files only, with backups and undo.\n")
            for name, description in COMPONENTS.items():
                print(f"  {name:12} {description}")
            value = input("\nComponents (comma-separated) [gtk,libadwaita]: ").strip()
            if value:
                selected = components(value) | set(previous.get("components", []))
            enabled = ask(
                "Select the theme for your current desktop?",
                bool(os.environ.get("XDG_CURRENT_DESKTOP")),
            )
            print(
                "Flatpak setup is optional and applies only to the app IDs entered below."
            )
            value = input(
                "Flatpak app IDs, comma-separated; optional =modern/=legacy/=gtk3 [none]: "
            ).strip()
            if value:
                args.flatpak = (args.flatpak or []) + [
                    item.strip() for item in value.split(",") if item.strip()
                ]
            print(
                "System-wide installation is separate: sudo ./install.sh install --system --dry-run"
            )
        plan = Plan(directories, store.state, system=args.system)
        if args.system and "libadwaita" in selected:
            plan.directory_roots.append(directories["config"] / "gtk-4.0")
        target = directories["data"] / "themes" / THEME
        shell_mode = args.shell_version or previous.get("shell_version", "auto")
        shell_version = shell_variant(shell_mode, "shell" in selected)
        if enabled and "shell" in selected:
            detected = shell_variant("auto", True)
            if detected != shell_version:
                raise InstallError(
                    "The requested Shell stylesheet does not match the local GNOME Shell version."
                )
        runtime(plan, target, shell_version)
        if "libadwaita" in selected:
            libadwaita(plan, target, mode)
        extras(plan, target, selected)
        activation(plan, selected, enabled, os.environ.get("XDG_CURRENT_DESKTOP", ""))
        flatpaks = sandbox.selections(
            args.flatpak, previous.get("flatpak", {}), InstallError
        )
        if flatpaks:
            sandbox.configure(globals(), plan, target, flatpaks)
        options = {
            "components": sorted(selected),
            "gtk4_mode": mode,
            "shell_version": shell_mode,
            "shell_variant": shell_version,
            "activate": enabled,
            "source": str(ROOT),
            "flatpak": flatpaks,
            "system": args.system,
        }
    print(f"\n{action.capitalize()} plan:")
    plan.show()
    if args.dry_run:
        print("Dry run: nothing changed.")
        return 0
    if not args.yes and not (sys.stdin.isatty() and ask("Apply this plan?")):
        print("Nothing installed. Use --yes after reviewing --dry-run.")
        return 2
    store.transact(plan, options=options, uninstall=action == "uninstall")
    print(
        "Finished. Restart affected applications. Backups are retained. Only the displayed user/system files, desktop preferences and explicitly selected Flatpak permissions were managed; no system packages or GDM configuration were changed."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (InstallError, OSError, ValueError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
