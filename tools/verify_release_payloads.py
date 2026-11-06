"""Read-only preflight: bind release manifests/checksums to actual upload bytes.

Run before contacting the release API. Does not repair metadata or touch games.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_release_payloads(dist, manifest_names=('patch_manifest.json', 'android_patch_manifest.json')):
    dist = Path(dist).resolve()
    checked = []

    def local_file(name):
        target = (dist / name).resolve()
        if not target.is_relative_to(dist) or not target.is_file():
            raise ValueError(f'Missing/unsafe release payload: {name}')
        return target

    def verify_bytes(label, size, digest, actual_size, actual_digest):
        if size != actual_size or digest != actual_digest:
            raise ValueError(f'Release metadata mismatch: {label}; '
                             f'expected {size}/{digest}, actual {actual_size}/{actual_digest}')

    for manifest_name in manifest_names:
        manifest = json.loads(local_file(manifest_name).read_text(encoding='utf-8-sig'))
        raw_files = manifest['files']
        files = ({**v, 'path': k} for k, v in raw_files.items()) if isinstance(raw_files, dict) else iter(raw_files)
        files = list(files)
        if not files:
            raise ValueError(f'Empty release manifest: {manifest_name}')
        if 'total_size' in manifest and manifest['total_size'] != sum(f['size'] for f in files):
            raise ValueError(f'Release total_size mismatch: {manifest_name}')
        package = manifest.get('package_zip')
        archive = None
        if package:
            package_path = local_file(package['filename'])
            verify_bytes(package['filename'], package.get('size_bytes', package.get('size')),
                         package['sha256'], package_path.stat().st_size, sha256_file(package_path))
            archive = zipfile.ZipFile(package_path)
        try:
            for entry in files:
                path = entry['path']
                if '/AssetBundles/' in path:
                    if archive is None:
                        raise ValueError(f'No declared package for bundle: {path}')
                    source = entry.get('source', path)
                    options = (source, path, Path(source).name, 'AssetBundles/' + Path(source).name)
                    member = next((name for name in options if name in archive.namelist()), None)
                    if member is None:
                        raise ValueError(f'Missing package member: {path}')
                    data = archive.read(member)
                    actual_size, actual_digest = len(data), hashlib.sha256(data).hexdigest()
                    bundle_alias = manifest.get('bundles', {}).get(Path(path).name)
                    if bundle_alias:
                        verify_bytes(path + ' bundles alias', bundle_alias['size_bytes'],
                                     bundle_alias['patched_sha256'], actual_size, actual_digest)
                else:
                    source = entry.get('source')
                    if not source:
                        source = {'data.arcx': 'data_patched_vi.arcx',
                                  'lua.arcx': 'lua_patched_vi.arcx'}.get(Path(path).name)
                    if not source:
                        raise ValueError(f'Missing release source: {path}')
                    target = local_file(source)
                    actual_size, actual_digest = target.stat().st_size, sha256_file(target)
                verify_bytes(manifest_name + ':' + path, entry['size'], entry['sha256'],
                             actual_size, actual_digest)
                for alias in ('data_arcx', 'lua_arcx'):
                    extra = manifest.get(alias)
                    if extra and extra.get('path') == path:
                        verify_bytes(manifest_name + ':' + alias, extra.get('size_bytes', extra.get('size')),
                                     extra['sha256'], actual_size, actual_digest)
                checked.append({'manifest': manifest_name, 'path': path, 'size': actual_size,
                                'sha256': actual_digest})
        finally:
            if archive is not None:
                archive.close()

    sums = local_file('SHA256SUMS.txt').read_text(encoding='utf-8-sig')
    entries = {}
    for line in sums.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line)
        if not match or match[2] in entries:
            raise ValueError('Invalid/duplicate SHA256SUMS entry')
        entries[match[2]] = match[1].lower()
    required = set(manifest_names)
    for row in checked:
        if row['path'].endswith('/data.arcx'):
            required.add('data_patched_vi.arcx')
        elif row['path'].endswith('/lua.arcx'):
            required.add('lua_patched_vi.arcx')
    for name in manifest_names:
        package = json.loads(local_file(name).read_text(encoding='utf-8-sig')).get('package_zip')
        if package:
            required.add(package['filename'])
    if required - entries.keys():
        raise ValueError('Missing SHA256SUMS entries: ' + ', '.join(sorted(required - entries.keys())))
    for name, expected in entries.items():
        if sha256_file(local_file(name)) != expected:
            raise ValueError(f'SHA256SUMS mismatch: {name}')
    return {'status': 'passed', 'files_verified': len(checked), 'checksums_verified': len(entries),
            'manifests': list(manifest_names), 'files': checked}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=Path(__file__).resolve().parents[1] / 'dist')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = verify_release_payloads(args.dist)
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False))
