"""Verified offline resource storage shared by the Stella downloader."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
import urllib.parse
import urllib.request


def safe_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError(f'Unsafe path: {value!r}')
    value = value.removeprefix('/')
    parts = value.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{p}{n}' for p in ('COM', 'LPT') for n in range(1, 10)}
    if any(not x or x in ('.', '..') or x.endswith((' ', '.')) or
           any(ord(c) < 32 or c in '<>"|?*' for c in x) or
           x.split('.')[0].upper() in reserved for x in parts):
        raise ValueError(f'Unsafe path: {value!r}')
    return PurePosixPath(*parts)


def version_component(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:[._-][0-9]+)*', value):
        raise ValueError(f'Invalid version: {value!r}')
    return value


def crc_table():
    table = []
    for n in range(256):
        for _ in range(8):
            n = (n >> 1) ^ (0xC96C5795D7870F42 if n & 1 else 0)
        table.append(n)
    return table


CRC_TABLE = crc_table()


def crc_update(crc, data):
    for byte in data:
        crc = CRC_TABLE[(crc ^ byte) & 255] ^ (crc >> 8)
    return crc


def fingerprints(path, algorithm):
    sha = hashlib.sha256()
    digest = hashlib.md5() if algorithm == 'md5' else None
    crc, size = 0xffffffffffffffff, 0
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(block)
            sha.update(block)
            if digest:
                digest.update(block)
            elif algorithm == 'crc64':
                crc = crc_update(crc, block)
    expected = digest.hexdigest() if digest else str(crc ^ 0xffffffffffffffff)
    return size, expected, sha.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.json-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def selected(path, profile):
    p = safe_path(path)
    if p.name.lower() in ('data.arcx', 'lua.arcx') or p.suffix.lower() == '.srt':
        return True
    return profile == 'localization' and 'installresource' in str(p).lower() and p.suffix.lower() == '.unity3d'


def manifest_records(text):
    """Read full files only; $BIN_DIFF_PATCH_FILE records are not full resources."""
    headers, records = {}, []
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith('$'):
            k, _, v = line.partition(':')
            if k in ('$CLIENT_VER', '$GAME_VER', '$RES_VER'):
                headers[k[1:]] = version_component(v)
            continue
        fields = line.split('|')
        if len(fields) < 4:
            raise ValueError('Invalid resource manifest record')
        name, md5, size, group = fields[:4]
        safe_path(name)
        if not re.fullmatch('[0-9a-fA-F]{32}', md5) or not size.isdigit():
            raise ValueError('Invalid checksum/size in resource manifest')
        records.append({'name': name, 'checksum': md5.lower(), 'algorithm': 'md5',
                        'size': int(size), 'group': group})
    if set(headers) != {'CLIENT_VER', 'GAME_VER', 'RES_VER'}:
        raise ValueError('Resource manifest lacks CLIENT_VER, GAME_VER or RES_VER')
    return headers, records


def contained(root, relative):
    destination = root.joinpath(*safe_path(relative).parts)
    if not destination.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output escapes snapshot directory')
    return destination


def validate_plan(plan, depth=0):
    if depth > 64:
        raise ValueError('Delta dependency chain is too deep or cyclic')
    seen = set()
    for item in plan['files']:
        name = str(safe_path(item['path'])).casefold()
        if name in seen:
            raise ValueError('Duplicate output path: ' + name)
        seen.add(name)
        if item['algorithm'] not in ('md5', 'crc64') or int(item['size']) < 0:
            raise ValueError('Invalid verification metadata')
        if not item.get('checksum'):
            raise ValueError('Missing source checksum')
        if item['algorithm'] == 'md5' and not re.fullmatch('[0-9a-f]{32}', str(item['checksum'])):
            raise ValueError('Invalid MD5 checksum')
        if item['algorithm'] == 'crc64' and (not str(item['checksum']).isdigit() or not 0 <= int(item['checksum']) < 2**64):
            raise ValueError('Invalid CRC64 checksum')
        if name.endswith('.part'):
            raise ValueError('Reserved staging suffix')
        if urllib.parse.urlparse(item['url']).scheme != 'https':
            raise ValueError('Resource URL must use HTTPS')
        if 'base' in item or 'patch' in item:
            if 'base' not in item or 'patch' not in item:
                raise ValueError('Delta requires both base and patch')
            validate_plan({'files': [dict(item['base'], path='base')]}, depth + 1)
            validate_plan({'files': [dict(item['patch'], path='patch')]}, depth + 1)


def transfer(item, destination, opener=urllib.request.urlopen):
    """Keep a bounded .part file, validate Range and verify before atomic commit."""
    size = int(item['size'])
    if destination.exists():
        actual, check, sha = fingerprints(destination, item['algorithm'])
        if actual == size and check == item['checksum']:
            return {'sha256': sha, 'reused': True}
        raise ValueError(f'Existing file differs from source: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + '.part')
    if part.is_symlink():
        raise ValueError('Refusing symlink partial file')
    offset = part.stat().st_size if part.exists() else 0
    if size == 0 and not part.exists():
        part.touch()
    if offset > size:
        raise ValueError('Partial file exceeds manifest size')
    if offset != size:
        headers = {'User-Agent': 'StellaResourceFetch/2.0', 'Accept-Encoding': 'identity'}
        if offset:
            headers['Range'] = f'bytes={offset}-'
        req = urllib.request.Request(item['url'], headers=headers)
        with opener(req, timeout=30) as response:
            if offset and response.status == 206:
                content_range = response.headers.get('Content-Range', '')
                if content_range != f'bytes {offset}-{size-1}/{size}':
                    raise ValueError('Unexpected Content-Range')
            elif response.status == 200:
                offset = 0
            else:
                raise ValueError('Unexpected response status')
            with open(part, 'ab' if offset else 'wb') as stream:
                count = offset
                for block in iter(lambda: response.read(1024 * 1024), b''):
                    count += len(block)
                    if count > size:
                        raise ValueError('Download exceeds manifest size')
                    stream.write(block)
    actual, check, sha = fingerprints(part, item['algorithm'])
    if actual != size or check != item['checksum']:
        # Remove corrupt complete payload so the next run can retry from zero.
        if actual == size:
            part.unlink()
        raise ValueError(f'Checksum/size mismatch: {destination.name}')
    os.rename(part, destination)
    return {'sha256': sha, 'reused': False}


def guard_snapshot(plan, root):
    root = Path(root)
    plan_file = root / 'plan.json'
    if plan_file.exists():
        previous = json.loads(plan_file.read_text(encoding='utf-8'))
        # Observation times/HTTP cache headers can change; payload identity cannot.
        identity = ('region', 'client_version', 'game_version', 'resource_version',
                    'manifest_sha256', 'profile', 'selection', 'files')
        stable = lambda p: {k: p.get(k) for k in identity}
        if stable(previous) != stable(plan):
            raise ValueError('Snapshot source/selection changed; choose a new output directory')


def materialize(item, destination, inputs, depth=0):
    if depth > 64:
        raise ValueError('Delta dependency chain is too deep')
    if 'patch' not in item:
        return transfer(item, destination)
    if destination.exists():
        actual, checksum, sha = fingerprints(destination, item['algorithm'])
        if actual == item['size'] and checksum == item['checksum']:
            return {'sha256': sha, 'reused': True, 'reconstructed': True}
        raise ValueError('Existing reconstructed file differs from source')
    from stella_bspatch import apply
    base_path = inputs / (item['base']['checksum'] + '.base')
    patch_path = inputs / (item['patch']['checksum'] + '.delta')
    materialize(item['base'], base_path, inputs, depth + 1)
    transfer(item['patch'], patch_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.reconstruct-', dir=destination.parent)
    os.close(fd)
    os.unlink(temporary)
    try:
        apply(base_path, patch_path, temporary, item['size'])
        actual, checksum, sha = fingerprints(temporary, item['algorithm'])
        if actual != item['size'] or checksum != item['checksum']:
            raise ValueError('Reconstructed file checksum/size differs from latest manifest')
        os.rename(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'sha256': sha, 'reused': False, 'reconstructed': True}


def sync(plan, root):
    validate_plan(plan)
    root = Path(root)
    payload_root = root / 'files'
    guard_snapshot(plan, root)
    # Validate every path before any payload writes.
    for item in plan['files']:
        contained(payload_root, item['path'])
    receipt = {k: v for k, v in plan.items() if k not in ('files', 'manifest_snapshots', 'evidence')}
    receipt.update(status='downloading', planned_files=len(plan['files']), plan_file='plan.json', results=[])
    atomic_json(root / 'plan.json', plan)
    atomic_json(root / 'receipt.json', receipt)
    try:
        for index, item in enumerate(plan['files'], 1):
            destination = contained(payload_root, item['path'])
            last_error = None
            for attempt in range(3):
                try:
                    result = materialize(item, destination, root / 'inputs')
                    break
                except (OSError, ValueError) as exc:
                    last_error = exc
                    if attempt == 2:
                        raise
                    time.sleep(1)
            receipt['results'].append(dict(path=item['path'], **result))
            atomic_json(root / 'receipt.json', receipt)
            print(f'[{index}/{len(plan["files"])}] {item["path"]}', flush=True)
    except Exception as exc:
        receipt.update(status='incomplete', error=str(exc))
        atomic_json(root / 'receipt.json', receipt)
        raise
    receipt['status'] = 'complete_for_manifest'
    atomic_json(root / 'receipt.json', receipt)
    return receipt
