"""Published archives must match tag data; no tagged build code may execute."""
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package as packaging
import verify_release as verifier


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'user.name=Release verifier test',
                                   '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                                   '-c', 'core.hooksPath=/dev/null', *args], cwd=root, stderr=subprocess.DEVNULL)


def build(root, target):
    before_root, before_argv = packaging.ROOT, sys.argv
    try:
        packaging.ROOT = root;sys.argv = ['package.py', str(target)]
        with contextlib.redirect_stdout(io.StringIO()):packaging.main()
    finally:
        packaging.ROOT, sys.argv = before_root, before_argv


class ReleaseVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='amoled-verifier-tests-')
        cls.base = Path(cls.temporary.name);cls.source = cls.base / 'original';cls.source.mkdir()
        for name in packaging.runtime_paths(ROOT) + packaging.accent_paths(ROOT):
            target = cls.source / name;target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        # A tagged script is deliberately hostile. The verifier must only use
        # the current trusted packager, treating the tag's files as inert data.
        (cls.source / 'tools').mkdir()
        (cls.source / 'tools/package.py').write_text('raise RuntimeError("TAG CODE EXECUTED")\n')
        git(cls.source, 'init', '-q');git(cls.source, 'add', '.')
        git(cls.source, 'commit', '-qm', 'fixture')
        git(cls.source, 'tag', 'v99.0.0')
        git(cls.source, 'tag', '-a', 'v99.0.1', '-m', 'Annotated fixture')
        cls.archive = cls.base / 'original.tar.gz';build(cls.source, cls.archive)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.base))
        self.addCleanup(shutil.rmtree, self.work)

    def clone(self):
        root = self.work / 'repository'
        git(self.base, 'clone', '-q', '--local', str(self.source), str(root))
        return root

    def verify(self, root, tag='v99.0.0', archive=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return verifier.verify_archive(root, tag, archive or self.archive)

    def test_exact_archive_and_lightweight_or_annotated_tag_pass_without_tag_code(self):
        for tag in ('v99.0.0', 'v99.0.1'):
            report = self.verify(self.source, tag)
            self.assertEqual(report['source_match'], 'byte-for-byte')
            self.assertFalse(report['tag_code_executed'])
            self.assertGreater(report['checksum_entries'], report['files'])
            self.assertEqual(report['commit'], git(self.source, 'rev-parse', 'HEAD').decode().strip())

    def test_corrupt_or_missing_archive_fails(self):
        damaged = self.work / 'bad.tar.gz';data = bytearray(self.archive.read_bytes());data[-1] ^= 1
        damaged.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'differs from tagged source'):
            self.verify(self.source, archive=damaged)
        with self.assertRaises(FileNotFoundError):self.verify(self.source, archive=self.work / 'absent.tar.gz')

    def test_archive_from_different_source_commit_fails(self):
        root = self.clone();(root / 'README.md').write_text('Different release source\n')
        git(root, 'add', 'README.md');git(root, 'commit', '-qm', 'change')
        git(root, 'tag', 'v99.0.2')
        with self.assertRaisesRegex(ValueError, 'differs from tagged source'):
            self.verify(root, 'v99.0.2')

    def test_unknown_or_unsafe_tags_fail(self):
        for name in ('main', '../../elsewhere', '--help', 'v99.0.0;echo nope'):
            with self.assertRaisesRegex(ValueError, 'stable tag'):self.verify(self.source, name)
        with self.assertRaisesRegex(ValueError, 'Command failed'):self.verify(self.source, 'v99.9.9')

    def test_self_consistent_package_with_bad_internal_icon_manifest_fails(self):
        root = self.clone();manifest = root / 'extra/icons/Adwaita-AMOLED/SHA256SUMS'
        text = manifest.read_text();manifest.write_text('0' * 64 + text[64:])
        git(root, 'add', '.');git(root, 'commit', '-qm', 'bad internal checksum');git(root, 'tag', 'v99.0.2')
        archive = self.work / 'bad-manifest.tar.gz';build(root, archive)
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):self.verify(root, 'v99.0.2', archive)

    def test_invalid_checksum_paths_and_duplicate_entries_are_rejected(self):
        digest = '0' * 64
        for text in (digest + '  ../escape\n', digest + '  /absolute\n',
                     digest + '  ok\n' + digest + '  ok\n', ''):
            with self.assertRaises(ValueError):verifier.verify_manifest(text.encode(), lambda _: b'content')

    def test_runtime_symlink_is_rejected_without_reading_its_target(self):
        root = self.clone();readme = root / 'README.md';readme.unlink()
        target = self.work / 'private.txt';target.write_text('untouched')
        readme.symlink_to(target)
        git(root, 'add', '.');git(root, 'commit', '-qm', 'linked payload');git(root, 'tag', 'v99.0.2')
        with self.assertRaises((ValueError, SystemExit, tarfile.FilterError)):
            self.verify(root, 'v99.0.2')
        self.assertEqual(target.read_text(), 'untouched')


if __name__ == '__main__':unittest.main(verbosity=2)
