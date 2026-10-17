"""Opt-in, selected-app Flatpak configuration and granular permission undo."""

import base64
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


class KeyFile:
    """Use Flatpak's GLib key-file format, including escaped filesystem lists."""

    def __init__(self, text):
        self.lib = ctypes.CDLL(
            ctypes.util.find_library("glib-2.0") or "libglib-2.0.so.0"
        )
        declarations = {
            "g_key_file_new": (ctypes.c_void_p, []),
            "g_key_file_unref": (None, [ctypes.c_void_p]),
            "g_key_file_load_from_data": (
                ctypes.c_int,
                [
                    ctypes.c_void_p,
                    ctypes.c_char_p,
                    ctypes.c_size_t,
                    ctypes.c_int,
                    ctypes.c_void_p,
                ],
            ),
            "g_key_file_has_key": (
                ctypes.c_int,
                [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p],
            ),
            "g_key_file_get_string_list": (
                ctypes.POINTER(ctypes.c_char_p),
                [
                    ctypes.c_void_p,
                    ctypes.c_char_p,
                    ctypes.c_char_p,
                    ctypes.POINTER(ctypes.c_size_t),
                    ctypes.c_void_p,
                ],
            ),
            "g_key_file_set_string_list": (
                None,
                [
                    ctypes.c_void_p,
                    ctypes.c_char_p,
                    ctypes.c_char_p,
                    ctypes.POINTER(ctypes.c_char_p),
                    ctypes.c_size_t,
                ],
            ),
            "g_key_file_get_string": (
                ctypes.c_void_p,
                [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p],
            ),
            "g_key_file_remove_key": (
                ctypes.c_int,
                [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p],
            ),
            "g_key_file_to_data": (
                ctypes.c_void_p,
                [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p],
            ),
            "g_strfreev": (None, [ctypes.POINTER(ctypes.c_char_p)]),
            "g_free": (None, [ctypes.c_void_p]),
        }
        for name, (result, args) in declarations.items():
            function = getattr(self.lib, name)
            function.restype = result
            function.argtypes = args
        self.pointer = self.lib.g_key_file_new()
        data = text.encode()
        if text and not self.lib.g_key_file_load_from_data(
            self.pointer, data, len(data), 3, None
        ):
            self.close()
            raise ValueError(
                "Cannot parse existing GLib/Flatpak configuration; no files changed."
            )

    def close(self):
        if self.pointer:
            self.lib.g_key_file_unref(self.pointer)
            self.pointer = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def has(self, group, key):
        return bool(
            self.lib.g_key_file_has_key(
                self.pointer, group.encode(), key.encode(), None
            )
        )

    def string(self, group, key):
        if not self.has(group, key):
            return None
        pointer = self.lib.g_key_file_get_string(
            self.pointer, group.encode(), key.encode(), None
        )
        if not pointer:
            raise ValueError("Invalid GLib string in configuration.")
        try:
            return ctypes.string_at(pointer).decode()
        finally:
            self.lib.g_free(pointer)

    def filesystems(self):
        if not self.has("Context", "filesystems"):
            return []
        count = ctypes.c_size_t()
        values = self.lib.g_key_file_get_string_list(
            self.pointer, b"Context", b"filesystems", ctypes.byref(count), None
        )
        if not values:
            raise ValueError("Invalid Flatpak filesystem list.")
        try:
            return [values[i].decode() for i in range(count.value)]
        finally:
            self.lib.g_strfreev(values)

    def set_filesystems(self, values):
        array = (ctypes.c_char_p * len(values))(*(value.encode() for value in values))
        self.lib.g_key_file_set_string_list(
            self.pointer, b"Context", b"filesystems", array, len(values)
        )
        length = ctypes.c_size_t()
        pointer = self.lib.g_key_file_to_data(self.pointer, ctypes.byref(length), None)
        if not pointer:
            raise ValueError("Cannot serialize Flatpak filesystem permissions.")
        try:
            return ctypes.string_at(pointer, length.value).decode()
        finally:
            self.lib.g_free(pointer)


def section(text, group, key):
    """Locate an unambiguous key without reformatting other user settings."""
    headers = list(
        re.finditer(r"(?m)^[ \t]*\[" + re.escape(group) + r"\][ \t]*\r?(?:\n|$)", text)
    )
    if len(headers) > 1:
        raise ValueError(f"Duplicate [{group}] sections need manual resolution.")
    if not headers:
        return None, None
    start = headers[0].end()
    following = re.search(r"(?m)^[ \t]*\[", text[start:])
    end = start + following.start() if following else len(text)
    keys = list(
        re.finditer(
            r"(?m)^[ \t]*" + re.escape(key) + r"[ \t]*=[^\n]*(?:\n|$)", text[start:end]
        )
    )
    if len(keys) > 1:
        raise ValueError(f"Duplicate {key} assignments need manual resolution.")
    assignment = (start + keys[0].start(), start + keys[0].end()) if keys else None
    return start, assignment


def render_filesystems(text, values, original_had_key=True):
    with KeyFile(text) as keyfile:
        serialized = keyfile.set_filesystems(values)
    _, output = section(serialized, "Context", "filesystems")
    line = serialized[slice(*output)] if values or original_had_key else ""
    start, existing = section(text, "Context", "filesystems")
    if existing:
        return text[: existing[0]] + line + text[existing[1] :]
    if not line:
        return text
    if start is not None:
        return text[:start] + line + text[start:]
    return (
        text + ("" if not text or text.endswith("\n") else "\n") + "[Context]\n" + line
    )


def identity(value):
    value = value.removeprefix("!")
    for ending in [":ro", ":rw", ":create"]:
        if value.endswith(ending):
            value = value[: -len(ending)]
            break
    if value.startswith("home/"):
        value = "~/" + value[5:]
    return value.rstrip("/") or "/"


def permission_map(values):
    result = {}
    for value in values:
        key = identity(value)
        if key in result:
            raise ValueError(
                "Duplicate filesystem permission paths need manual resolution."
            )
        result[key] = value
    return result


def selections(values, previous, error):
    selected = dict(previous)
    for value in values or []:
        app, separator, mode = value.partition("=")
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2,}", app):
            raise error(
                "Flatpak app IDs must have at least three dot-separated components, without paths: "
                + app
            )
        mode = mode if separator else "auto"
        if mode not in ["auto", "modern", "legacy", "gtk3"]:
            raise error("Flatpak mode must be auto, modern, legacy or gtk3: " + value)
        selected[app] = mode
    return selected


def library_version(files):
    """GTK's upstream Meson library version: 1.(binary_age-interface_age).interface_age.

    binary_age = 100*minor+micro. No host library is loaded and no runtime code is
    executed. Unversioned/repacked libraries require an explicit mode instead.
    """
    found = []
    present = False
    for base in [files / "lib", files / "lib64"]:
        if not base.is_dir():
            continue
        for path in base.rglob("libgtk-4.so.1*"):
            present = True
            match = re.fullmatch(r"libgtk-4\.so\.1\.(\d+)\.(\d+)", path.name)
            if not match or path.is_symlink() or not path.is_file():
                continue
            if not path.resolve().is_relative_to(files.resolve()):
                continue
            with path.open("rb") as stream:
                if stream.read(4) != b"\x7fELF":
                    continue
            age = int(match[1]) + int(match[2])
            found.append((4, age // 100, age % 100))
    versions = set(found)
    if len(versions) > 1:
        raise ValueError(
            "Multiple GTK4 library versions found; select an explicit Flatpak mode."
        )
    return next(iter(versions)) if versions else None, present


def detect_mode(core, executable, app, requested):
    command, error = core["command"], core["InstallError"]
    app_location = Path(command([executable, "info", "--show-location", app]))
    runtime = command([executable, "info", "--show-runtime", app])
    runtime_location = Path(
        command([executable, "info", "--show-location", "runtime/" + runtime])
    )
    version = None
    present = False
    for files in [app_location / "files", runtime_location / "files"]:
        version, present = library_version(files)
        if present:
            break
    if requested == "auto":
        if version is not None:
            return ("modern" if version >= (4, 16, 0) else "legacy"), version, runtime
        if present:
            raise error(
                f"Cannot determine bundled GTK4 version for {app}; choose {app}=modern or {app}=legacy explicitly after checking it."
            )
        gtk3 = any(
            p.is_file()
            for files in [app_location / "files", runtime_location / "files"]
            for base in [files / "lib", files / "lib64"]
            if base.is_dir()
            for p in base.rglob("libgtk-3.so.0*")
        )
        if gtk3:
            return "gtk3", None, runtime
        raise error(
            f"No standard GTK library found for {app}; Qt/non-GTK apps are not covered. Choose an explicit mode only for a verified GTK app."
        )
    if requested == "modern" and version is not None and version < (4, 16, 0):
        raise error(
            f"{app} uses GTK {version}; modern CSS needs GTK 4.16+. Use auto or legacy."
        )
    return requested, version, runtime


def canonical_grants(core, executable, app, targets):
    # Ask Flatpak's actual parser to encode/normalize its own filesystem tokens.
    with tempfile.TemporaryDirectory(prefix="amoled-flatpak-plan-") as temporary:
        env = dict(os.environ, FLATPAK_USER_DIR=temporary)
        core["command"](
            [
                executable,
                "override",
                "--user",
                *[
                    "--filesystem="
                    + target.replace("\\", "\\\\").replace(":", "\\:")
                    + ":ro"
                    for target in targets
                ],
                app,
            ],
            env=env,
        )
        with KeyFile((Path(temporary) / "overrides" / app).read_text()) as keyfile:
            return keyfile.filesystems()


def ini_setting(core, plan, path, group, key, value, component):
    text = plan.base_text(path)
    with KeyFile(text):
        pass
    start, assignment = section(text, group, key)
    inserted = core["block"](key + "=" + value)
    if assignment:
        begin, end = assignment
        original = text[begin:end]
        updated = text[:begin] + inserted + text[end:]
        fragments = [{"block": inserted, "restore": original}]
    elif start is not None:
        updated = text[:start] + inserted + text[start:]
        fragments = [{"block": inserted, "restore": ""}]
    else:
        updated, fragments = core["append_fragment"](
            text, "[" + group + "]\n" + key + "=" + value
        )
    with KeyFile(updated) as keyfile:
        if keyfile.string(group, key) != value:
            raise ValueError("Cannot safely manage " + str(path))
    plan.put(path, updated.encode(), component, fragments)


def configure(core, plan, target, apps):
    executable = shutil.which("flatpak")
    if not executable:
        raise core["InstallError"]("Install Flatpak before selecting --flatpak.")
    location, read_text, error = (
        core["location"],
        core["read_text"],
        core["InstallError"],
    )
    user_dir = location(
        os.environ.get("FLATPAK_USER_DIR") or str(plan.roots["data"] / "flatpak"),
        "FLATPAK_USER_DIR",
    )
    plan.allowed.append(user_dir / "overrides")
    for app, requested in sorted(apps.items()):
        mode, version, runtime = detect_mode(core, executable, app, requested)
        effective = core["command"]([executable, "info", "--show-permissions", app])
        with KeyFile(effective) as keyfile:
            if keyfile.string("Environment", "XDG_CONFIG_HOME") is not None:
                raise error(
                    f"{app} overrides XDG_CONFIG_HOME; configure its GTK stylesheet manually."
                )
            for grant in keyfile.filesystems():
                key = identity(grant)
                if not grant.startswith("!") and (
                    key == "xdg-config"
                    or key == "xdg-config/gtk-4.0"
                    or key.startswith("xdg-config/gtk-4.0/")
                ):
                    raise error(
                        f"{app} shares host GTK4 configuration. Remove that mapping before per-app setup so runtime-specific CSS can be used."
                    )
        override = user_dir / "overrides" / app
        core["guard"](override, plan.allowed)
        text = read_text(override)
        with KeyFile(text) as keyfile:
            values = keyfile.filesystems()
            had_key = keyfile.has("Context", "filesystems")
        current = permission_map(values)
        previous = plan.state["files"].get(str(override), {})
        old = (previous.get("metadata") or {}).get("flatpak", {})
        old_grants = old.get("grants", {})
        for key, record in old_grants.items():
            if current.get(key) != record["after"]:
                raise error(
                    f"Flatpak theme permission was changed after setup: {app} / {key}. Resolve it before updating."
                )
        targets = ["xdg-data/themes/Adwaita-AMOLED", str(target)]
        grants = permission_map(canonical_grants(core, executable, app, targets))
        records = dict(old_grants)
        for key, after in grants.items():
            records[key] = {
                "before": old_grants.get(key, {}).get("before", current.get(key)),
                "after": after,
            }
        updated_values = [
            value for value in values if identity(value) not in grants
        ] + list(grants.values())
        updated = render_filesystems(text, updated_values)
        metadata = {
            "flatpak": {
                "app": app,
                "grants": records,
                "had_key": old.get("had_key", had_key),
            }
        }
        plan.put(override, updated.encode(), "flatpak-override", metadata=metadata)
        app_config = plan.roots["home"] / ".var/app" / app / "config"
        ini_setting(
            core,
            plan,
            app_config / "gtk-3.0/settings.ini",
            "Settings",
            "gtk-theme-name",
            "Adwaita-AMOLED",
            "flatpak-css",
        )
        if mode != "gtk3":
            core["libadwaita"](
                plan,
                target,
                mode,
                path=app_config / "gtk-4.0/gtk.css",
                component="flatpak-css",
            )
        plan.messages.append(
            f'Flatpak {app}: {mode}; runtime {runtime}; GTK library version {version or "explicit/GTK3"}. Uses per-app configuration and two read-only theme mappings; no global override or GTK_THEME export.'
        )


def undo_override(core, path, record, current):
    if core["summary"](current) == record["after"] and not record.get("external_edits"):
        return record["before"]
    if current["kind"] != "file":
        raise core["InstallError"](
            "Flatpak override changed type; keeping it: " + str(path)
        )
    text = core["read_text"](path)
    with KeyFile(text) as keyfile:
        values = keyfile.filesystems()
    actual = permission_map(values)
    metadata = record["metadata"]["flatpak"]
    for key, grant in metadata["grants"].items():
        if actual.get(key) != grant["after"]:
            raise core["InstallError"](
                "Flatpak theme permission was changed; keeping it: "
                + str(path)
                + " / "
                + key
            )
    wanted_values = [
        value for value in values if identity(value) not in metadata["grants"]
    ]
    wanted_values += [
        grant["before"]
        for grant in metadata["grants"].values()
        if grant["before"] is not None
    ]
    updated = render_filesystems(text, wanted_values, metadata["had_key"])
    data = updated.encode()
    return dict(
        core["desired"](data, current["mode"]), data=base64.b64encode(data).decode()
    )
