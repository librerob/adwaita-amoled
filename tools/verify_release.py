#!/usr/bin/env python3
"""Verify an uploaded runtime archive using tagged source as data, never code."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

import package as packaging

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'librerob/adwaita-amoled'
TAG = re.compile(r'v\d+\.\d+\.\d+')
RELATIVE = re.compile(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*')


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError('Command failed: ' + ' '.join(str(a) for a in args[:4]))
    return result.stdout


def valid_path(name):
    return bool(RELATIVE.fullmatch(name)) and all(p not in ('.', '..') for p in name.split('/'))


def verify_manifest(data, resolve):
    seen = set()
    for line in data.decode('utf-8').splitlines():
        digest, separator, name = line.partition('  ')
        if not separator or not re.fullmatch('[0-9a-f]{64}', digest) or not valid_path(name) or name in seen:
            raise ValueError('Invalid checksum manifest entry')
        seen.add(name)
        if hashlib.sha256(resolve(name)).hexdigest() != digest:
            raise ValueError('Checksum mismatch: ' + name)
    if not seen:
        raise ValueError('Empty checksum manifest')
    return len(seen)


def source_file(root, name):
    if not valid_path(name):raise ValueError('Invalid manifest path')
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents) if p != root) or not path.is_file():
        raise ValueError('Missing or linked payload file: ' + name)
    return path.read_bytes()


def verify_archive(repository, tag, archive):
    if not TAG.fullmatch(tag):raise ValueError('Expected a stable tag such as v1.9.0')
    commit = command(['git', 'rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}'], repository).decode().strip()
    tree = command(['git', 'rev-parse', f'{commit}^{{tree}}'], repository).decode().strip()
    with tempfile.TemporaryDirectory(prefix='amoled-release-verify-') as temporary:
        work = Path(temporary);source = work / 'source';source.mkdir()
        # No checkout hooks, build scripts, installers or Python from the tag run.
        exported = command(['git', 'archive', '--format=tar', commit], repository)
        with tarfile.open(fileobj=io.BytesIO(exported)) as bundle:
            bundle.extractall(source, filter='data')
        old_root, old_argv = packaging.ROOT, sys.argv
        rebuilt = work / 'rebuilt.tar.gz'
        try:
            packaging.ROOT = source
            sys.argv = ['package.py', str(rebuilt)]
            packaging.main()  # Trusted verifier checkout's packager, not tag code.
        finally:
            packaging.ROOT, sys.argv = old_root, old_argv
        expected = hashlib.sha256(rebuilt.read_bytes()).hexdigest()
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Uploaded archive differs from tagged source: expected SHA-256 {expected}; got {actual}')
        checks = 0
        # Validate every included source SHA256SUMS, including sparse overlays.
        for manifest in source.rglob('SHA256SUMS'):
            relative = manifest.relative_to(source)
            if not (str(relative).startswith('accents/') or str(relative).startswith('extra/icons/')):
                continue
            def resolve(name, directory=manifest.parent):
                path = directory / name
                if path.is_file():return source_file(source, str(path.relative_to(source)))
                # An accent icon manifest includes shared base files as well as
                # changed overlay files; check the merged installed view.
                parts = path.relative_to(source).parts
                if len(parts) > 2 and parts[0] == 'accents':
                    return source_file(source, '/'.join(parts[2:]))
                raise ValueError('Missing manifest file: ' + name)
            checks += verify_manifest(source_file(source, str(relative)), resolve)
        with tarfile.open(rebuilt, 'r:gz') as bundle:
            members = bundle.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)) or any(not m.isfile() or not m.name.startswith('Adwaita-AMOLED/') for m in members):
                raise ValueError('Invalid archive member layout')
            def payload(name):
                member = bundle.getmember('Adwaita-AMOLED/' + name)
                return bundle.extractfile(member).read()
            checks += verify_manifest(payload('ARCHIVE_CONTENTS.sha256'), payload)
        return {'tag': tag, 'commit': commit, 'tree': tree, 'sha256': actual,
                'bytes': archive.stat().st_size, 'files': len(members), 'checksum_entries': checks,
                'source_match': 'byte-for-byte', 'tag_code_executed': False}


def verify_published(repository, tag):
    route = f'repos/{REPOSITORY}/releases/tags/{tag}' if tag else f'repos/{REPOSITORY}/releases/latest'
    release = json.loads(command(['gh', 'api', route]))
    tag = release['tag_name']
    if release['draft'] or release['prerelease'] or not TAG.fullmatch(tag):
        raise ValueError('Expected a published stable release')
    expected_name = f'Adwaita-AMOLED-{tag}.tar.gz'
    assets = [a for a in release['assets'] if a['name'] == expected_name]
    if len(assets) != 1:raise ValueError('Expected exactly one uploaded asset: ' + expected_name)
    asset = assets[0]
    if asset['state'] != 'uploaded' or not 0 < asset['size'] <= 64 * 1024 * 1024:
        raise ValueError('Release asset is incomplete or exceeds the verifier size limit')
    with tempfile.TemporaryDirectory(prefix='amoled-release-download-') as temporary:
        command(['gh', 'release', 'download', tag, '--repo', REPOSITORY,
                 '--pattern', expected_name, '--dir', temporary])
        archive = Path(temporary) / expected_name
        if archive.stat().st_size != asset['size']:raise ValueError('Downloaded asset size mismatch')
        digest = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
        if asset.get('digest') and asset['digest'] != digest:raise ValueError('GitHub asset digest mismatch')
        report = verify_archive(repository, tag, archive)
    report.update(release_url=release['html_url'], asset=expected_name, github_digest=asset.get('digest'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        if args.tag and not TAG.fullmatch(args.tag):raise ValueError('Expected a stable tag such as v1.9.0')
        report = verify_published(ROOT, args.tag)
        report['result'] = 'PASS'
        summary = (f"# Release verification: PASS\n\n[{report['tag']}]({report['release_url']})\n\n"
                   f"- Uploaded archive matches tagged source byte-for-byte.\n- All included checksum manifests passed.\n"
                   f"- Commit: `{report['commit']}`\n- Tree: `{report['tree']}`\n- SHA-256: `{report['sha256']}`\n"
                   f"- Files: {report['files']}; checksum entries: {report['checksum_entries']}.\n\n"
                   'No release or repository files were changed. This is an integrity check, not a new rendering test.\n')
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.TimeoutExpired, SystemExit) as error:
        report = {'result': 'FAIL', 'error': str(error)}
        summary = '# Release verification: FAIL\n\n' + str(error) + '\n'
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.output / 'verification.md').write_text(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:stream.write(summary)
    print(summary)
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
