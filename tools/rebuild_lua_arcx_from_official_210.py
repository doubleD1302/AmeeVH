#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild dist/lua_patched_vi.arcx on top of the OFFICIAL game 2.1.x lua.arcx.

The previous Vietnamese lua.arcx was built from the 2.0.x scripts, so a 2.1.x client ran
outdated game logic (and was missing 34 script files).  This tool starts from the official
2.1.x scripts and re-applies the Vietnamese text as string-constant replacements (the same
mechanism patch_all_lua_avg.py uses), from three sources, in this order of precedence:

  1. overlay rows  (2.1.0 delivery / extra translations): {"id": "2.1.0:lua:<hash>:<locator>",
     "source": {"source_text": ...}, "text_vi": ..., "status": ...}  -> per script file
  2. pairs recovered from the old Vietnamese build: for every script the old VI archive changed
     versus the pure 2.0.0 English archive, constants are paired index-by-index (or aligned with
     difflib when the old build also changed code)               -> per script file
  3. a global English->Vietnamese fallback (only for dialogue-like strings: >= 8 chars with a space)

Hand-made *code* patches in the old build (a few dorm/guide scripts) are NOT carried over:
those scripts come from the official 2.1.x archive, only their text is re-applied.

Usage:
  python tools/rebuild_lua_arcx_from_official_210.py --official <lua.arcx> --old-vi <old lua_patched_vi.arcx>
         --en-orig <pure 2.0.0 English lua.arcx> --overlay <jsonl> [--overlay ...] --out <file>
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto  # noqa: E402
from tools.arcx_adapter import ArcxArchive, repack_archive, xxtea_decrypt, xxtea_encrypt, XXTEA_KEY  # noqa: E402

STR_KINDS = (4, 20)


def load(path: Path):
    arc = ArcxArchive(path)
    raw = path.read_bytes()
    return arc, {e["hash"]: (e, arc.extract_entry(e, raw)) for e in arc.entries}


def parse(enc: bytes):
    chunk = Lua53Chunk(xxtea_decrypt(enc, XXTEA_KEY))
    hdr = chunk.read_bytes(33)
    up = chunk.read_byte()
    return hdr, up, chunk.parse_proto()


def flat_consts(proto, out):
    out.extend(proto["constants"])
    for child in proto["protos"]:
        flat_consts(child, out)
    return out


def sval(c):
    kind, val = c
    if kind in STR_KINDS:
        try:
            return val[1].decode("utf-8")
        except Exception:
            return None
    return None


def collect_pairs(orig_enc: bytes, vi_enc: bytes):
    co = flat_consts(parse(orig_enc)[2], [])
    cv = flat_consts(parse(vi_enc)[2], [])
    pairs = {}
    if len(co) == len(cv):
        spans = [(0, len(co), 0, len(cv))]
    else:  # the old build also changed code: align on the constant sequence
        so = [repr(sval(c)) if sval(c) is not None else repr(c) for c in co]
        sv = [repr(sval(c)) if sval(c) is not None else repr(c) for c in cv]
        spans = [(a, b, c, d) for tag, a, b, c, d in
                 difflib.SequenceMatcher(None, so, sv, autojunk=False).get_opcodes()
                 if tag == "replace" and b - a == d - c]
    for a, b, c, d in spans:
        for x, y in zip(co[a:b], cv[c:d]):
            s1, s2 = sval(x), sval(y)
            if s1 is not None and s2 is not None and s1 != s2 and s1.strip():
                pairs[s1.strip()] = s2.strip()
    return pairs


def load_overlay(paths):
    per_file = collections.defaultdict(dict)
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            parts = str(r.get("id", "")).split(":", 3)
            vi = (r.get("text_vi") or "").strip()
            src = ((r.get("source") or {}).get("source_text") or "").strip()
            if len(parts) != 4 or parts[1] != "lua" or not vi or not src or r.get("status") == "Giữ EN":
                continue
            per_file[int(parts[2], 16)][src] = vi
    return per_file


def patch_proto(proto, table, used):
    new = []
    for kind, val in proto["constants"]:
        if kind in STR_KINDS:
            try:
                s = val[1].decode("utf-8")
            except Exception:
                s = None
            key = s.strip() if s is not None else None
            if key and key in table:
                lpad = len(s) - len(s.lstrip())
                rpad = len(s) - len(s.rstrip())
                data = (" " * lpad + table[key] + " " * rpad).encode("utf-8")
                n = len(data) + 1
                new.append((kind, (0xFF if n >= 0xFF else n, data)))
                used.add(key)
                continue
        new.append((kind, val))
    proto["constants"] = new
    for child in proto["protos"]:
        patch_proto(child, table, used)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--official", required=True, type=Path)
    ap.add_argument("--old-vi", required=True, type=Path)
    ap.add_argument("--en-orig", required=True, type=Path)
    ap.add_argument("--overlay", action="append", type=Path, default=[])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    off_arc, off = load(args.official)
    _, old = load(args.old_vi)
    _, orig = load(args.en_orig)
    overlay = load_overlay(args.overlay)

    file_pairs = {}
    for h, (_, enc) in old.items():
        if h in orig and enc != orig[h][1]:
            try:
                p = collect_pairs(orig[h][1], enc)
            except Exception:
                continue
            if p:
                file_pairs[h] = p
    votes = collections.defaultdict(collections.Counter)
    for p in file_pairs.values():
        for en, vi in p.items():
            if len(en) >= 8 and " " in en:
                votes[en][vi] += 1
    global_table = {en: c.most_common(1)[0][0] for en, c in votes.items()}
    print(f"pairs from old build: {len(file_pairs)} files, {sum(map(len, file_pairs.values()))} strings; "
          f"global fallback {len(global_table)}; overlay files {len(overlay)}")

    work = Path(tempfile.mkdtemp(prefix="lua210_"))
    entries_dir = work / "entries"
    entries_dir.mkdir()
    manifest = {"archive_name": "lua.arcx", "version": off_arc.version, "flag": off_arc.flag,
                "entry_count": off_arc.entry_count, "payload_decrypted": False, "entries": []}
    stats = collections.Counter()
    for h in sorted(off, key=lambda x: off[x][0]["index"]):
        e, enc = off[h]
        payload = enc
        try:
            hdr, up, proto = parse(enc)
        except Exception:
            stats["unparsed_kept_official"] += 1
            proto = None
        if proto is not None:
            table = dict(global_table)
            table.update(file_pairs.get(h, {}))
            table.update(overlay.get(h, {}))
            used = set()
            patch_proto(proto, table, used)
            if used:
                payload = xxtea_encrypt(hdr + bytes([up]) + serialize_proto(proto), XXTEA_KEY)
                stats["files_patched"] += 1
                stats["strings_replaced_distinct"] += len(used)
            if h in overlay:
                stats["overlay_rows"] += len(overlay[h])
                stats["overlay_rows_applied"] += sum(1 for k in overlay[h] if k in used)
        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        (entries_dir / fname).write_bytes(payload)
        manifest["entries"].append({"index": e["index"], "hash": h, "hash_hex": e["hash_hex"], "filename": fname,
                                    "origin_size": len(payload), "payload_size": len(payload)})
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp_out = work / "lua_patched_vi.arcx"
    repack_archive(work, tmp_out, encrypt_payload=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp_out, args.out)
    print(json.dumps(dict(stats)))
    print(f"wrote {args.out} size={args.out.stat().st_size} sha256={hashlib.sha256(args.out.read_bytes()).hexdigest()}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
