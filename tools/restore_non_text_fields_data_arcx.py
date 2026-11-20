#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore non-text (code/ID) values that a Vietnamese data.arcx changed versus the official table.

rebuild_data_arcx_from_official_210.py keeps any value that differs from the official English text as
"translated".  For Story.<id>.4 (the stage label/code shown on story nodes) that kept swapped codes:
Story.1116.4 '15'->'BT02', Story.1117.4 'BT02'->'15', Story.1121.4 '19'->'BT03', Story.1122.4 'BT03'->'19'.

This tool compares --vi with --official and puts the official value back wherever the official value is a
pure code (letters/digits only, no spaces, <= 6 chars, contains a digit) AND the key is Story.<id>.4.  Every
other entry is copied byte-for-byte.  Writes only --out.

  python tools/restore_non_text_fields_data_arcx.py --official <official data.arcx> --vi dist/data_patched_vi.arcx --out <file>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive, xxtea_decrypt, xxtea_encrypt, XXTEA_KEY  # noqa: E402

CODE = re.compile(r"^(?=.*\d)[A-Za-z0-9]{1,6}$")
# Only keys known to hold codes (never display text). UIText.* values such as "2D"/"1h" ARE text.
KEYS = re.compile(r"^/Story\.\d+\.4$")


def load(path):
    arc = ArcxArchive(path)
    raw = Path(path).read_bytes()
    out = {}
    for e in arc.entries:
        enc = arc.extract_entry(e, raw)
        try:
            plain = xxtea_decrypt(enc, XXTEA_KEY)
        except Exception:
            plain = enc
        out[e["hash"]] = (e, enc, plain)
    return arc, out


def fix(off_v, vi_v, path, log):
    if isinstance(off_v, dict) and isinstance(vi_v, dict):
        for k in vi_v:
            if k in off_v:
                vi_v[k] = fix(off_v[k], vi_v[k], path + "/" + k, log)
        return vi_v
    if isinstance(off_v, list) and isinstance(vi_v, list) and len(off_v) == len(vi_v):
        return [fix(a, b, f"{path}/{i}", log) for i, (a, b) in enumerate(zip(off_v, vi_v))]
    if isinstance(off_v, str) and isinstance(vi_v, str) and off_v != vi_v and KEYS.match(path) and CODE.match(off_v):
        log.append((path, vi_v, off_v))
        return off_v
    return vi_v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--official", required=True, type=Path)
    ap.add_argument("--vi", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    arc, off = load(a.official)
    _, vi = load(a.vi)
    work = Path(tempfile.mkdtemp(prefix="datafix_"))
    (work / "entries").mkdir()
    manifest = {"archive_name": "data.arcx", "version": arc.version, "flag": arc.flag,
                "entry_count": arc.entry_count, "payload_decrypted": False, "entries": []}
    changed = []
    for h in sorted(off, key=lambda x: off[x][0]["index"]):
        e = off[h][0]
        _, enc, plain = vi[h]
        try:
            data = json.loads(plain.decode("utf-8"))
        except Exception:
            data = None
        if isinstance(data, dict):
            odata = json.loads(off[h][2].decode("utf-8"))
            log = []
            fixed = fix(odata, data, "", log)
            if log:
                changed.extend((e["hash_hex"], *l) for l in log)
                enc = xxtea_encrypt(json.dumps(fixed, ensure_ascii=False, indent=2).encode("utf-8"), XXTEA_KEY)
        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        (work / "entries" / fname).write_bytes(enc)
        manifest["entries"].append({"index": e["index"], "hash": h, "hash_hex": e["hash_hex"], "filename": fname,
                                    "origin_size": len(enc), "payload_size": len(enc)})
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp = work / "out.arcx"
    repack_archive(work, tmp, encrypt_payload=False)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp, a.out)
    shutil.rmtree(work, ignore_errors=True)
    for c in changed:
        print("restored", c)
    print(f"{len(changed)} values restored; wrote {a.out} size={a.out.stat().st_size} sha256={hashlib.sha256(a.out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
