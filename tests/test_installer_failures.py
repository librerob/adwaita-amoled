"""Failure injection against the real Bash entry point, in disposable directories."""

import os
import resource
from pathlib import Path
import shutil
import shlex
import signal
import time
import sys
import tarfile
import subprocess
import unittest
import test_installer as base


class InstallerFailureTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    write = base.InstallerTests.write
    fake_program = base.InstallerTests.fake_program

    def installed_marker(self):
        path = self.theme / "previous-working-theme"
        self.write(path, "previous version\n")
        return path

    def source_copy(self):
        source = self.base / "source"
        shutil.copytree(
            base.ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        return source

    def test_copy_failure_preserves_existing_theme(self):
        marker = self.installed_marker()
        self.fake_program("cp", 'echo "simulated copy failure" >&2; exit 1')
        self.run_cli(success=False)
        self.assertEqual(marker.read_text(), "previous version\n")

    def test_missing_resource_stops_before_changing_existing_theme(self):
        marker = self.installed_marker()
        source = self.source_copy()
        (source / "gtk-3.0/gtk.gresource").unlink()
        self.run_cli(root=source, success=False)
        self.assertEqual(marker.read_text(), "previous version\n")

    def test_invalid_nvim_profile_does_not_block_unrelated_gtk_installation(self):
        env = dict(self.env, NVIM_APPNAME="invalid/profile")
        self.run_cli(env=env)
        self.assertTrue((self.theme / "gtk-3.0/gtk.gresource").is_file())
        before = (self.theme / "gtk-3.0/gtk.gresource").read_bytes()
        self.run_cli("--extras", "nvim", env=env, success=False)
        self.assertEqual((self.theme / "gtk-3.0/gtk.gresource").read_bytes(), before)

    def assert_no_staging_left(self):
        self.assertFalse(list(self.theme.parent.glob(".Adwaita-AMOLED-install.*")))

    def test_first_install_copy_failure_does_not_leave_a_partial_theme(self):
        self.fake_program("cp", 'echo "simulated disk-full copy failure" >&2; exit 1')
        self.run_cli(success=False)
        self.assertFalse(self.theme.exists())
        self.assert_no_staging_left()

    def test_late_copy_failure_keeps_existing_theme_and_cleans_staging(self):
        marker = self.installed_marker()
        real_cp = shlex.quote(shutil.which("cp"))
        self.fake_program(
            "cp", "[[ $* != *gtk-4.0* ]] || exit 23\nexec " + real_cp + ' "$@"'
        )
        self.run_cli(success=False)
        self.assertEqual(marker.read_text(), "previous version\n")
        self.assert_no_staging_left()

    def test_prepare_permission_failure_preserves_existing_theme(self):
        marker = self.installed_marker()
        self.fake_program("chmod", 'echo "simulated permission failure" >&2; exit 1')
        self.run_cli(success=False)
        self.assertEqual(marker.read_text(), "previous version\n")
        self.assert_no_staging_left()

    def test_rename_failure_before_and_after_new_directory_is_moved_restores_old_theme(
        self,
    ):
        real_mv = shlex.quote(shutil.which("mv"))
        for when in ["before", "after"]:
            with self.subTest(when=when):
                marker = self.installed_marker()
                action = "exit 23" if when == "before" else real_mv + ' "$@"; exit 23'
                self.fake_program(
                    "mv",
                    "if [[ $3 == */new ]]; then "
                    + action
                    + "; fi\nexec "
                    + real_mv
                    + ' "$@"',
                )
                self.run_cli(success=False)
                self.assertEqual(marker.read_text(), "previous version\n")
                self.assert_no_staging_left()

    def test_missing_copy_tool_is_reported_before_changing_theme(self):
        marker = self.installed_marker()
        bin_dir = self.base / "minimal-bin"
        bin_dir.mkdir()
        for name in [
            "bash",
            "dirname",
            "realpath",
            "rm",
            "mkdir",
            "ln",
            "chmod",
            "mv",
            "mktemp",
            "flock",
            "stat",
        ]:
            (bin_dir / name).symlink_to(shutil.which(name))
        env = dict(self.env, PATH=str(bin_dir))
        result = subprocess.run(
            ["/bin/bash", str(base.ROOT / "install.sh")],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing: cp", result.stderr)
        self.assertEqual(marker.read_text(), "previous version\n")

    def test_archive_corruption_is_rejected_before_overwriting_theme(self):
        marker = self.installed_marker()
        archive = self.base / "runtime.tar.gz"
        subprocess.run(
            [sys.executable, str(base.ROOT / "tools/package.py"), str(archive)],
            check=True,
            capture_output=True,
        )
        with tarfile.open(archive) as package:
            package.extractall(self.base / "package", filter="data")
        source = self.base / "package" / base.THEME
        (source / "gtk-3.0/gtk.css").write_text("corrupted CSS")
        result = self.run_cli(root=source, success=False)
        self.assertIn("checksum verification failed", result.stderr)
        self.assertEqual(marker.read_text(), "previous version\n")

    def wait_for_marker(self, marker, process):
        deadline = time.monotonic() + 10
        while (
            not marker.exists()
            and time.monotonic() < deadline
            and process.poll() is None
        ):
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "Installer did not reach the injected pause")

    def paused_installer(self, phase):
        ready = self.base / ("ready-" + str(time.monotonic_ns()))
        real_mv = shlex.quote(shutil.which("mv"))
        real_cp = shlex.quote(shutil.which("cp"))
        self.env["TEST_READY"] = str(ready)
        if phase == "copy":
            self.fake_program(
                "cp", 'touch "$TEST_READY"\nsleep 30\nexec ' + real_cp + ' "$@"'
            )
        else:
            self.fake_program(
                "mv",
                "if [[ $4 == */previous ]]; then "
                + real_mv
                + ' "$@"; touch "$TEST_READY"; sleep 30; exit 0; fi\nexec '
                + real_mv
                + ' "$@"',
            )
        process = subprocess.Popen(
            ["bash", str(base.ROOT / "install.sh")],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        self.addCleanup(lambda: self.stop_process(process))
        self.wait_for_marker(ready, process)
        return process

    def stop_process(self, process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=10)

    def test_sigterm_during_copy_preserves_previous_theme(self):
        marker = self.installed_marker()
        process = self.paused_installer("copy")
        os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=10)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(marker.read_text(), "previous version\n")
        self.assert_no_staging_left()

    def test_sigterm_between_directory_renames_restores_previous_theme(self):
        marker = self.installed_marker()
        process = self.paused_installer("rename")
        os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=10)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(marker.read_text(), "previous version\n")
        self.assert_no_staging_left()

    def test_concurrent_install_is_rejected_without_touching_the_active_copy(self):
        marker = self.installed_marker()
        process = self.paused_installer("copy")
        env = dict(self.env, PATH=os.environ["PATH"])
        result = self.run_cli(env=env, success=False)
        self.assertIn("Another installer is using this destination", result.stderr)
        self.assertEqual(marker.read_text(), "previous version\n")
        os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=10)
        self.assert_no_staging_left()

    def test_kernel_file_size_limit_write_failure_keeps_old_theme(self):
        marker = self.installed_marker()

        def limit_writes():
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))

        result = subprocess.run(
            ["bash", str(base.ROOT / "install.sh")],
            env=self.env,
            capture_output=True,
            text=True,
            preexec_fn=limit_writes,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "previous version\n")
        self.assert_no_staging_left()

    def test_interrupt_and_terminal_hangup_restore_previous_theme(self):
        for signum in [signal.SIGINT, signal.SIGHUP]:
            with self.subTest(signal=signum):
                marker = self.installed_marker()
                process = self.paused_installer("rename")
                os.killpg(process.pid, signum)
                process.communicate(timeout=10)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(marker.read_text(), "previous version\n")
                self.assert_no_staging_left()

    def test_failed_restore_retains_original_files_and_reports_recovery_location(self):
        marker = self.installed_marker()
        real_mv = shlex.quote(shutil.which("mv"))
        self.fake_program(
            "mv",
            "if [[ $3 == */new || $3 == */previous ]]; then exit 23; fi\nexec "
            + real_mv
            + ' "$@"',
        )
        result = self.run_cli(success=False)
        previous = list(
            self.theme.parent.glob(
                ".Adwaita-AMOLED-install.*/previous/previous-working-theme"
            )
        )
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous[0].read_text(), "previous version\n")
        self.assertIn("retained at", result.stderr)

    def test_gtk_detection_ignores_stdout_from_failed_package_queries(self):
        self.fake_program("pkg-config", "exit 1")
        self.fake_program("dpkg-query", 'echo "package is not installed"; exit 1')
        self.fake_program("rpm", 'echo "package gtk4 is not installed"; exit 1')
        self.fake_program("pacman", 'echo "gtk4 4.24.1"')
        self.run_cli("-l")
        self.assertEqual(
            (self.config / "gtk-4.0/gtk.css").resolve().name, "gtk-modern.css"
        )

    def test_empty_essential_file_is_rejected_by_installer_and_packager(self):
        marker = self.installed_marker()
        source = self.source_copy()
        (source / "gtk-2.0/gtkrc").write_bytes(b"")
        self.run_cli(root=source, success=False)
        self.assertEqual(marker.read_text(), "previous version\n")
        archive = self.base / "invalid.tar.gz"
        result = subprocess.run(
            [sys.executable, str(source / "tools/package.py"), str(archive)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(archive.exists())


if __name__ == "__main__":
    from report import main

    main()
