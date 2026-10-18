"""Runtime selection is identical for checkout installs and release archives."""

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import unittest

import test_installer as base


class RuntimePackageTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    write = base.InstallerTests.write

    def package(self, source=base.ROOT, success=True):
        archive = self.base / "runtime.tar.gz"
        result = subprocess.run(
            [sys.executable, str(source / "tools/package.py"), str(archive)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return archive

    def source_copy(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        return source

    def test_incomplete_or_linked_accent_distribution_blocks_packaging(self):
        source = self.source_copy()
        manifest = source / "accents/SHA256SUMS"
        original = manifest.read_text()
        manifest.write_text(
            "\n".join(
                line
                for line in original.splitlines()
                if not line.split("  ")[1].startswith("purple/")
            )
            + "\n"
        )
        self.assertFalse(self.package(source, success=False).exists())
        manifest.unlink()
        self.assertFalse(self.package(source, success=False).exists())
        manifest.symlink_to(base.ROOT / "accents/SHA256SUMS")
        self.assertFalse(self.package(source, success=False).exists())

    def test_archive_and_checkout_install_have_identical_runtime_files(self):
        self.run_cli("--shell-version", "51")
        with tarfile.open(self.package()) as tar:
            tar.extractall(self.base / "extracted", filter="data")
        source = self.base / "extracted" / base.THEME
        listed = set((source / "runtime-files.txt").read_text().splitlines())
        installed = {
            str(p.relative_to(self.theme)) for p in self.theme.rglob("*") if p.is_file()
        }
        archived = {
            str(p.relative_to(source)) for p in source.rglob("*") if p.is_file()
        }
        self.assertEqual(installed, listed)
        distributed_accents = {
            str(p.relative_to(source))
            for p in (source / "accents").rglob("*")
            if p.is_file()
        }
        self.assertEqual(
            archived, listed | {"ARCHIVE_CONTENTS.sha256"} | distributed_accents
        )
        self.assertFalse((self.theme / "accents").exists())
        for name in listed:
            self.assertEqual(
                (self.theme / name).read_bytes(), (source / name).read_bytes(), name
            )
        for line in (source / "ARCHIVE_CONTENTS.sha256").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(
                hashlib.sha256((source / name).read_bytes()).hexdigest(), digest
            )
        self.run_cli("--shell-version", "46", root=source)
        self.assertEqual(
            (self.theme / "gnome-shell/gnome-shell.css").read_bytes(),
            (base.ROOT / "gnome-shell/gnome-shell-46.css").read_bytes(),
        )

    def test_runtime_keeps_assets_wallpaper_licenses_and_omits_build_and_promo_files(
        self,
    ):
        with tarfile.open(self.package()) as tar:
            tar.extractall(self.base / "extracted", filter="data")
        root = self.base / "extracted" / base.THEME
        for name in [
            "extra/wallpaper/blackmount.png",
            "LICENSE",
            "gnome-shell/COPYING.LGPL",
            "gnome-shell/sass/upstream/COPYING",
            "gnome-shell/sass/46/upstream/COPYING",
        ]:
            self.assertEqual(
                (root / name).read_bytes(), (base.ROOT / name).read_bytes()
            )
        for name in [
            "src",
            "tools",
            "tests",
            "palette",
            "extra/logo",
            "extra/screenshot",
            "gnome-shell/build.sh",
        ]:
            self.assertFalse((root / name).exists(), name)
        self.assertFalse(list(root.rglob("*.scss")))
        for path in root.rglob("*"):
            if path.is_relative_to(root / "accents"):
                continue  # Overlays resolve unchanged assets after installation.
            if path.suffix not in (".css", ".qss", ".rasi"):
                continue
            text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
            for url in re.findall(r"""url\(\s*['"]?([^)'"\s]+)['"]?\s*\)""", text):
                if not re.match(r"(resource|data|https?):", url):
                    self.assertTrue((path.parent / url).is_file(), f"{path}: {url}")

    def test_missing_listed_asset_blocks_installer_and_packager_before_replacement(
        self,
    ):
        source = self.source_copy()
        (source / "extra/libadwaita/assets/check-symbolic.svg").unlink()
        marker = self.theme / "previous-version"
        self.write(marker, "keep")
        self.run_cli(root=source, success=False)
        self.assertEqual(marker.read_text(), "keep")
        self.assertFalse(self.package(source, success=False).exists())

    def test_malformed_or_incomplete_file_lists_are_rejected_without_mutation(self):
        source = self.source_copy()
        listing = source / "runtime-files.txt"
        original = listing.read_text()
        for changed in [
            original + "../outside\n",
            original + "/tmp/outside\n",
            original + "index.theme\n",
            original + "gtk-4.0/./gtk.css\n",
            original.replace("gtk-4.0/gtk.gresource\n", ""),
            original.replace("runtime-files.txt\n", ""),
            original.replace("setup-menu.sh\n", ""),
            "",
        ]:
            with self.subTest(listing=changed[-80:]):
                listing.write_text(changed)
                self.run_cli(root=source, success=False)
                self.assertFalse(self.theme.exists())
                self.assertFalse(self.package(source, success=False).exists())

    def test_linked_runtime_asset_is_rejected(self):
        source = self.source_copy()
        path = source / "extra/libadwaita/assets/check-symbolic.svg"
        path.unlink()
        path.symlink_to(base.ROOT / "extra/libadwaita/assets/check-symbolic.svg")
        self.run_cli(root=source, success=False)
        self.assertFalse(self.theme.exists())
        self.assertFalse(self.package(source, success=False).exists())


if __name__ == "__main__":
    from report import main

    main()
