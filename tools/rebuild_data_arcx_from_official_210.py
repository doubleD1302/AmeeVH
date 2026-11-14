#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild dist/data_patched_vi.arcx on top of the OFFICIAL game 2.1.0 data.arcx.

Why: v1.3.0 was produced by injecting 2.1.0 translations into the older (2.0.x)
data.arcx.  The JSON text tables were patched but every binary table
(bin/*.bytes, e.g. Gacha.bytes) stayed at 2.0.x, so the 2.1.0 server sent ids
(Gacha 10161, Activity 201021, CharacterSkin 10803, ...) that did not exist in the
local tables.  PlayerGachaData.CacheGachaData then threw "attempt to index a nil
value (local 'cfg')" and the recruitment (Chieu Mo) screen got stuck.

Method (data only; lua.arcx is untouched):
  * every entry/key set and every binary table comes from the official 2.1.0 file;
  * for each JSON text key, the existing Vietnamese value is kept when the current
    dist file holds a translation (value differs from the English source in
    2.0.0 / 2.0.2), otherwise the official English text is used.

Usage:
  python tools/rebuild_data_arcx_from_official_210.py --official <official data.arcx> [--out <file>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.arcx_adapter import ArcxArchive, repack_archive, xxtea_decrypt, xxtea_encrypt, XXTEA_KEY  # noqa: E402


def load(path: Path):
    arc = ArcxArchive(path)
    raw = path.read_bytes()
    out = {}
    for e in arc.entries:
        enc = arc.extract_entry(e, raw)
        try:
            plain = xxtea_decrypt(enc, XXTEA_KEY)
        except Exception:
            plain = enc
        out[e["hash"]] = (e, enc, plain)
    return arc, out


def as_json(plain: bytes):
    try:
        d = json.loads(plain.decode("utf-8"))
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def merge_value(off_v, vi_v, base_vs, stats):
    """Recursively keep the Vietnamese text where one exists, else the official 2.1.0 value."""
    if isinstance(off_v, dict):
        vd = vi_v if isinstance(vi_v, dict) else {}
        bds = [b for b in base_vs if isinstance(b, dict)]
        return {k: merge_value(v, vd.get(k), [b.get(k) for b in bds], stats) for k, v in off_v.items()}
    if isinstance(off_v, list):
        vl = vi_v if isinstance(vi_v, list) and len(vi_v) == len(off_v) else None
        bls = [b for b in base_vs if isinstance(b, list) and len(b) == len(off_v)]
        return [merge_value(v, vl[i] if vl else None, [b[i] for b in bls], stats) for i, v in enumerate(off_v)]
    if isinstance(off_v, str):
        stats["keys"] += 1
        if isinstance(vi_v, str) and vi_v != off_v and vi_v not in base_vs:
            stats["vi_kept"] += 1
            return vi_v
        stats["en_fallback"] += 1
    return off_v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--official", required=True, type=Path)
    ap.add_argument("--vi", type=Path, default=ROOT / "dist" / "data_patched_vi.arcx")
    # Pure-English older archives used to tell "translated" from "still English".
    # NOTE: dist/vanilla/data_original_en.arcx is NOT usable here - it already holds Vietnamese text.
    ap.add_argument("--en-base", type=Path, action="append", default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "dist" / "data_patched_vi.arcx")
    args = ap.parse_args()
    if not args.en_base:
        args.en_base = [ROOT / "work" / "subagents" / "update_210_inventory_20261113_r01" / "catalog_crosscheck"
                        / "EN_2.0.2_2611061338" / "Tables" / "data.arcx"]

    off_arc, off = load(args.official)
    _, vi = load(args.vi)
    bases = [load(p)[1] for p in args.en_base if p.exists()]
    if not bases:
        print("ERROR: no English base archive found; refusing to guess translated keys", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="data210_"))
    entries_dir = work / "entries"
    entries_dir.mkdir()
    manifest = {"archive_name": "data.arcx", "version": off_arc.version, "flag": off_arc.flag,
                "entry_count": off_arc.entry_count, "payload_decrypted": False, "entries": []}

    stats = dict(json_entries=0, binary_entries=0, keys=0, vi_kept=0, en_fallback=0)
    for e, enc, plain in (off[h] for h in sorted(off, key=lambda h: off[h][0]["index"])):
        h = e["hash"]
        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        data = as_json(plain)
        if data is None:
            stats["binary_entries"] += 1
            payload = enc  # official bytes, still XXTEA-encrypted, untouched
        else:
            stats["json_entries"] += 1
            vi_json = as_json(vi[h][2]) if h in vi else None
            base_jsons = [as_json(b[h][2]) for b in bases if h in b]
            merged = {}
            for k, v in data.items():
                merged[k] = merge_value(v, vi_json.get(k) if vi_json else None,
                                        [bj.get(k) for bj in base_jsons if bj], stats)
            payload = xxtea_encrypt(json.dumps(merged, ensure_ascii=False, indent=2).encode("utf-8"), XXTEA_KEY)
        (entries_dir / fname).write_bytes(payload)
        manifest["entries"].append({"index": e["index"], "hash": h, "hash_hex": e["hash_hex"],
                                    "filename": fname, "origin_size": len(payload), "payload_size": len(payload)})
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    tmp_out = work / "data_patched_vi.arcx"
    repack_archive(work, tmp_out, encrypt_payload=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp_out, args.out)
    sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(json.dumps(stats))
    print(f"wrote {args.out} size={args.out.stat().st_size} sha256={sha}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
