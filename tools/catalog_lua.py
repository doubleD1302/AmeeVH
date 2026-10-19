#!/usr/bin/env python3
"""Recover original file names and directory tree for all Lua scripts in lua.arcx.

Extracts the debug source string from the Lua 5.3 bytecode header of each entry,
verifies the xxHash64 against the entry's hash in lua.arcx, and generates a
complete catalog of all Lua scripts.
"""

import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.test_pure_xxtea import xxtea_decrypt

XXTEA_KEY = bytes.fromhex("a9 21 a4 67 c7 d7 df 39 6e 60 90 9c 31 22 5b d2")

# Pure Python xxHash64 implementation
PRIME64_1 = 11400714785074694791
PRIME64_2 = 14029467366897019727
PRIME64_3 = 1609587929392839161
PRIME64_4 = 9650029242287828579
PRIME64_5 = 2870177450012600261
MASK64 = 0xFFFFFFFFFFFFFFFF

def _rotl(x: int, r: int) -> int:
    return (((x << r) & MASK64) | (x >> (64 - r))) & MASK64

def xxhash64_pure(data: bytes, seed: int = 0) -> int:
    length = len(data)
    idx = 0
    if length >= 32:
        v1 = (seed + PRIME64_1 + PRIME64_2) & MASK64
        v2 = (seed + PRIME64_2) & MASK64
        v3 = seed & MASK64
        v4 = (seed - PRIME64_1) & MASK64
        limit = length - 32
        while idx <= limit:
            k1, k2, k3, k4 = struct.unpack('<4Q', data[idx:idx+32])
            v1 = (_rotl((v1 + k1 * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
            v2 = (_rotl((v2 + k2 * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
            v3 = (_rotl((v3 + k3 * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
            v4 = (_rotl((v4 + k4 * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
            idx += 32
        def merge_round(h, v):
            v = (_rotl((v * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
            h = ((h ^ v) * PRIME64_1 + PRIME64_4) & MASK64
            return h
        h64 = (_rotl(v1, 1) + _rotl(v2, 7) + _rotl(v3, 12) + _rotl(v4, 18)) & MASK64
        h64 = merge_round(h64, v1)
        h64 = merge_round(h64, v2)
        h64 = merge_round(h64, v3)
        h64 = merge_round(h64, v4)
    else:
        h64 = (seed + PRIME64_5) & MASK64

    h64 = (h64 + length) & MASK64
    while idx + 8 <= length:
        k1 = struct.unpack('<Q', data[idx:idx+8])[0]
        k1 = (_rotl((k1 * PRIME64_2) & MASK64, 31) * PRIME64_1) & MASK64
        h64 = (_rotl((h64 ^ k1), 27) * PRIME64_1 + PRIME64_4) & MASK64
        idx += 8

    if idx + 4 <= length:
        k1 = struct.unpack('<I', data[idx:idx+4])[0]
        h64 = (_rotl((h64 ^ ((k1 * PRIME64_1) & MASK64)), 23) * PRIME64_2 + PRIME64_3) & MASK64
        idx += 4

    while idx < length:
        k1 = data[idx]
        h64 = (_rotl((h64 ^ ((k1 * PRIME64_5) & MASK64)), 11) * PRIME64_1) & MASK64
        idx += 1

    h64 ^= (h64 >> 33)
    h64 = (h64 * PRIME64_2) & MASK64
    h64 ^= (h64 >> 29)
    h64 = (h64 * PRIME64_3) & MASK64
    h64 ^= (h64 >> 32)
    return h64

def normalize_path(path: str) -> str:
    return path.lower().replace('\\', '/')

def parse_lua_header_source(data: bytes) -> Optional[str]:
    """Parse Proto source string from Lua 5.3 bytecode."""
    if len(data) < 36 or not data.startswith(b"\x1bLua"):
        return None
    offset = 34
    size_byte = data[offset]
    offset += 1
    if size_byte == 0:
        return ""
    elif size_byte == 0xFF:
        str_len = struct.unpack("<Q", data[offset : offset + 8])[0]
        offset += 8
    else:
        str_len = size_byte
    # in lua 5.3, string is str_len bytes (including null terminator or size is len+1)
    raw_str = data[offset : offset + str_len - 1]
    return raw_str.decode("utf-8", errors="replace")

def clean_source_path(src: str) -> str:
    """Convert absolute build source to relative game Lua path."""
    if src.startswith("@"):
        src = src[1:]
    # Replace backward slashes
    src = src.replace("\\", "/")
    # Look for Lua/
    idx = src.find("/Lua/")
    if idx != -1:
        return src[idx + 5:]
    if src.startswith("Lua/"):
        return src[4:]
    return src

def main():
    root = Path(__file__).parent.parent
    lua_unpacked_dir = root / "work" / "research" / "unpacked_lua"
    entries_dir = lua_unpacked_dir / "entries"
    manifest_path = lua_unpacked_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"Error: {manifest_path} does not exist", file=sys.stderr)
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    print(f"Loaded manifest with {len(entries)} Lua entries.")

    catalog = []
    matched_count = 0
    unmatched_count = 0
    non_lua_count = 0

    out_tree_dir = root / "work" / "research" / "lua_tree"
    out_tree_dir.mkdir(parents=True, exist_ok=True)

    for item in entries:
        idx = item["index"]
        expected_hash = item["hash"]
        fname = item["filename"]
        fpath = entries_dir / fname

        encrypted_data = fpath.read_bytes()
        decrypted_data = xxtea_decrypt(encrypted_data, XXTEA_KEY)

        src = parse_lua_header_source(decrypted_data)
        if not src:
            non_lua_count += 1
            catalog.append({
                "index": idx,
                "hash": expected_hash,
                "hash_hex": item["hash_hex"],
                "filename": fname,
                "lua_path": None,
                "verified": False,
                "note": "Non-Lua or stripped debug header"
            })
            continue

        rel_path = clean_source_path(src)
        # Check hash
        calc_hash = xxhash64_pure(normalize_path(rel_path).encode("utf-8"))
        is_verified = (calc_hash == expected_hash)

        if not is_verified:
            # Try with 'lua/' prefix
            calc_hash2 = xxhash64_pure(normalize_path(f"lua/{rel_path}").encode("utf-8"))
            if calc_hash2 == expected_hash:
                rel_path = f"lua/{rel_path}"
                is_verified = True

        if is_verified:
            matched_count += 1
        else:
            unmatched_count += 1

        # Save to tree
        target_file = out_tree_dir / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(decrypted_data)

        catalog.append({
            "index": idx,
            "hash": expected_hash,
            "hash_hex": item["hash_hex"],
            "raw_filename": fname,
            "rel_path": rel_path,
            "source_raw": src,
            "verified": is_verified,
            "payload_size": len(decrypted_data)
        })

    catalog_out = root / "work" / "research" / "lua_catalog.json"
    catalog_out.write_text(json.dumps({
        "total_entries": len(entries),
        "matched_and_verified": matched_count,
        "unmatched": unmatched_count,
        "non_lua": non_lua_count,
        "catalog": catalog
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n================ SUMMARY ================")
    print(f"Total entries:        {len(entries)}")
    print(f"Matched & Verified:   {matched_count} ({matched_count/len(entries)*100:.2f}%)")
    print(f"Unmatched hashes:     {unmatched_count}")
    print(f"Non-Lua / No header:  {non_lua_count}")
    print(f"Saved catalog to:     {catalog_out}")
    print(f"Exported tree to:     {out_tree_dir}")

if __name__ == "__main__":
    main()
