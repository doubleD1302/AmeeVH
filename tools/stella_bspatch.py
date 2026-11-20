"""Bounded BSDIFF40 reconstruction; never execute downloaded game content."""
import bz2
import io
from pathlib import Path


def number(data):
    if len(data) != 8:
        raise ValueError('Truncated BSDIFF integer')
    value = int.from_bytes(data, 'little') & ((1 << 63) - 1)
    return -value if data[7] & 128 else value


def apply(old_path, patch_path, output_path, expected_size):
    patch = Path(patch_path).read_bytes()
    if patch[:8] != b'BSDIFF40' or len(patch) < 32:
        raise ValueError('Unsupported delta format (expected BSDIFF40)')
    ctrl_size, diff_size, new_size = (number(patch[i:i+8]) for i in (8, 16, 24))
    if min(ctrl_size, diff_size, new_size) < 0 or new_size != expected_size or 32 + ctrl_size + diff_size > len(patch):
        raise ValueError('Invalid BSDIFF lengths')
    ctrl = bz2.BZ2File(io.BytesIO(patch[32:32+ctrl_size]))
    diff = bz2.BZ2File(io.BytesIO(patch[32+ctrl_size:32+ctrl_size+diff_size]))
    extra = bz2.BZ2File(io.BytesIO(patch[32+ctrl_size+diff_size:]))
    old_size = Path(old_path).stat().st_size
    old_pos, new_pos, operations = 0, 0, 0
    try:
        with open(old_path, 'rb') as old, open(output_path, 'xb') as out:
            while new_pos < new_size:
                operations += 1
                if operations > new_size + 1024:
                    raise ValueError('Too many BSDIFF control records')
                raw = ctrl.read(24)
                if len(raw) != 24:
                    raise ValueError('Truncated BSDIFF controls')
                add, insert, seek = (number(raw[i:i+8]) for i in (0, 8, 16))
                if add < 0 or insert < 0 or new_pos + add + insert > new_size:
                    raise ValueError('BSDIFF output bounds exceeded')
                remaining = add
                while remaining:
                    length = min(remaining, 1024 * 1024)
                    delta = diff.read(length)
                    if len(delta) != length:
                        raise ValueError('Truncated BSDIFF difference stream')
                    source = bytearray(length)
                    start, end = max(0, old_pos), min(old_size, old_pos + length)
                    if end > start:
                        old.seek(start)
                        source[start-old_pos:end-old_pos] = old.read(end-start)
                    out.write(bytes((a+b) & 255 for a, b in zip(source, delta)))
                    remaining -= length
                    old_pos += length
                    new_pos += length
                remaining = insert
                while remaining:
                    block = extra.read(min(remaining, 1024 * 1024))
                    if not block:
                        raise ValueError('Truncated BSDIFF extra stream')
                    out.write(block)
                    remaining -= len(block)
                    new_pos += len(block)
                old_pos += seek
            if ctrl.read(1) or diff.read(1) or extra.read(1):
                raise ValueError('Unexpected trailing BSDIFF data')
    finally:
        ctrl.close()
        diff.close()
        extra.close()
