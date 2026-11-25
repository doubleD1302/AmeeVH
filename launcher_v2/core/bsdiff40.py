# -*- coding: utf-8 -*-
"""Bounded BSDIFF40 reconstruction for official resource deltas.

The delta only describes how to rebuild an official file from another official file.
Nothing downloaded here is ever executed. Every length is checked against the
declared output size and the caller verifies the final MD5.
"""
from __future__ import annotations

import bz2
import io
from pathlib import Path

_BLOCK = 1024 * 1024
_ZERO_PROBE = 4096


class BsdiffError(ValueError):
    pass


def _number(data: bytes) -> int:
    if len(data) != 8:
        raise BsdiffError("Truncated BSDIFF integer")
    value = int.from_bytes(data, "little") & ((1 << 63) - 1)
    return -value if data[7] & 128 else value


def _add_block(source: bytes | bytearray, delta: bytes) -> bytes:
    """(source + delta) mod 256 with a fast path for the usual mostly-zero diff stream."""
    n = len(delta)
    out = bytearray(source)
    for start in range(0, n, _ZERO_PROBE):
        chunk = delta[start:start + _ZERO_PROBE]
        if chunk.count(0) == len(chunk):
            continue
        for i, d in enumerate(chunk, start):
            if d:
                out[i] = (out[i] + d) & 255
    return bytes(out)


def _bz_read(stream: bz2.BZ2File, size: int) -> bytes:
    try:
        return stream.read(size)
    except (OSError, EOFError) as exc:
        raise BsdiffError(f"Corrupt BSDIFF bz2 stream: {exc}") from exc


def apply_bsdiff(old_path: str | Path, patch_path: str | Path, output_path: str | Path, expected_size: int) -> None:
    patch = Path(patch_path).read_bytes()
    if len(patch) < 32 or patch[:8] != b"BSDIFF40":
        raise BsdiffError("Unsupported delta format (expected BSDIFF40)")
    ctrl_size, diff_size, new_size = (_number(patch[i:i + 8]) for i in (8, 16, 24))
    if min(ctrl_size, diff_size, new_size) < 0 or new_size != expected_size or 32 + ctrl_size + diff_size > len(patch):
        raise BsdiffError("Invalid BSDIFF lengths")
    try:
        ctrl = bz2.BZ2File(io.BytesIO(patch[32:32 + ctrl_size]))
        diff = bz2.BZ2File(io.BytesIO(patch[32 + ctrl_size:32 + ctrl_size + diff_size]))
        extra = bz2.BZ2File(io.BytesIO(patch[32 + ctrl_size + diff_size:]))
    except (OSError, EOFError) as exc:
        raise BsdiffError(f"Corrupt BSDIFF bz2 stream: {exc}") from exc
    old_size = Path(old_path).stat().st_size
    old_pos, new_pos, operations = 0, 0, 0
    out_file = Path(output_path)
    created_output = False
    try:
        with open(old_path, "rb") as old, open(out_file, "xb") as out:
            created_output = True
            while new_pos < new_size:
                operations += 1
                if operations > new_size + 1024:
                    raise BsdiffError("Too many BSDIFF control records")
                raw = _bz_read(ctrl, 24)
                if len(raw) != 24:
                    raise BsdiffError("Truncated BSDIFF controls")
                add, insert, seek = (_number(raw[i:i + 8]) for i in (0, 8, 16))
                if add < 0 or insert < 0 or new_pos + add + insert > new_size:
                    raise BsdiffError("BSDIFF output bounds exceeded")
                remaining = add
                while remaining:
                    length = min(remaining, _BLOCK)
                    delta = _bz_read(diff, length)
                    if len(delta) != length:
                        raise BsdiffError("Truncated BSDIFF difference stream")
                    source = bytearray(length)
                    start, end = max(0, old_pos), min(old_size, old_pos + length)
                    if end > start:
                        old.seek(start)
                        source[start - old_pos:end - old_pos] = old.read(end - start)
                    out.write(_add_block(source, delta))
                    remaining -= length
                    old_pos += length
                    new_pos += length
                remaining = insert
                while remaining:
                    block = _bz_read(extra, min(remaining, _BLOCK))
                    if not block:
                        raise BsdiffError("Truncated BSDIFF extra stream")
                    out.write(block)
                    remaining -= len(block)
                    new_pos += len(block)
                old_pos += seek
            if _bz_read(ctrl, 1) or _bz_read(diff, 1) or _bz_read(extra, 1):
                raise BsdiffError("Unexpected trailing BSDIFF data")
    except BaseException:
        if created_output:
            out_file.unlink(missing_ok=True)
        raise
    finally:
        for stream in (ctrl, diff, extra):
            try:
                stream.close()
            except OSError:
                pass
