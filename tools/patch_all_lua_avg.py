# -*- coding: utf-8 -*-
"""
Phase 4: Full Lua Bytecode Patcher & Packager for Stella Sora.
Patches all 626 Lua AVG story & phone chat files in lua_full_unpacked/entries.
Replaces constant strings with de-formalized Vietnamese dialogue.
Preserves 100% of engine commands, parameters, sound/voice cues.
Re-encrypts with XXTEA and repacks lua.arcx.
Deploys to Steam and Yostar clients.
"""

import json
from pathlib import Path
import struct
import shutil
import time
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto
from arcx_adapter import xxtea_decrypt, xxtea_encrypt, XXTEA_KEY, repack_archive, ArcxArchive

def patch_proto_constants(proto: dict, master_dict: dict, stats: dict):
    new_constants = []
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                s_strip = s.strip()
                if s_strip in master_dict:
                    new_text = master_dict[s_strip]
                    # Preserve original whitespace padding if any
                    l_pad = len(s) - len(s.lstrip())
                    r_pad = len(s) - len(s.rstrip())
                    full_new_text = (" " * l_pad) + new_text + (" " * r_pad)

                    new_s_bytes = full_new_text.encode('utf-8')
                    new_len = len(new_s_bytes) + 1
                    new_tag = 0xFF if new_len >= 0xFF else new_len
                    new_constants.append((ktype, (new_tag, new_s_bytes)))
                    stats['patched_strings'] += 1
                    continue
            except Exception:
                pass
        new_constants.append((ktype, val))

    proto['constants'] = new_constants

    for child in proto['protos']:
        patch_proto_constants(child, master_dict, stats)

def patch_lua_bytecode(raw_decrypted: bytes, master_dict: dict, stats: dict) -> bytes:
    chunk = Lua53Chunk(raw_decrypted)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()

    patch_proto_constants(proto, master_dict, stats)

    rebuilt_raw = hdr + bytes([size_up]) + serialize_proto(proto)
    return rebuilt_raw

def main():
    print("=== STARTING FULL LUA AVG DIALOGUE PATCHING ===")

    # 1. Build Master Translation Dictionary
    print("Loading all dialogue sources...")
    master_dict = {}

    # Source A: Approved Batches 1-4 (40,000 strings)
    batches = [
        "batch_10000_avg_clean.json", "batch_10000_avg_clean_b2.json",
        "batch_10000_avg_clean_b3.json", "batch_10000_avg_clean_b4.json"
    ]
    appr_batches = [
        "batch_10k_approved.json", "batch_10k_b2_approved.json",
        "batch_10k_b3_approved.json", "batch_10k_b4_approved.json"
    ]
    for en_f, vi_f in zip(batches, appr_batches):
        en_p = ROOT / "work" / "batches" / en_f
        vi_p = ROOT / "work" / "batches" / vi_f
        if en_p.exists() and vi_p.exists():
            en_d = json.load(open(en_p, encoding="utf-8"))
            vi_d = json.load(open(vi_p, encoding="utf-8"))
            for k, en in en_d.items():
                if k in vi_d:
                    master_dict[en.strip()] = vi_d[k].strip()

    print(f"Loaded {len(master_dict)} items from batches 1-4.")

    # Source B: Remaining translated dialogue (cache/output)
    rem_cache = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
    if rem_cache.exists():
        rem_d = json.load(open(rem_cache, encoding="utf-8"))
        master_dict.update({k.strip(): v.strip() for k, v in rem_d.items()})
        print(f"Total master dictionary size after remaining dialogue: {len(master_dict)}")

    # 2. Load Mapping of 626 Lua AVG files
    mapping_path = ROOT / "work" / "research" / "avg_file_to_entry.json"
    mapping = json.load(open(mapping_path, encoding="utf-8"))
    entries_dir = ROOT / "work" / "research" / "lua_full_unpacked" / "entries"

    stats = {
        'total_files': len(mapping),
        'patched_files': 0,
        'patched_strings': 0
    }

    t0 = time.time()
    for fname, info in mapping.items():
        entry_fname = info['filename']
        bin_path = entries_dir / entry_fname
        if not bin_path.exists():
            print(f"Warning: Entry not found: {bin_path}")
            continue

        encrypted_data = bin_path.read_bytes()
        decrypted_data = xxtea_decrypt(encrypted_data, XXTEA_KEY)

        prev_count = stats['patched_strings']
        patched_raw = patch_lua_bytecode(decrypted_data, master_dict, stats)
        num_in_file = stats['patched_strings'] - prev_count

        if num_in_file > 0:
            stats['patched_files'] += 1
            # Re-encrypt with XXTEA
            re_encrypted = xxtea_encrypt(patched_raw, XXTEA_KEY)
            bin_path.write_bytes(re_encrypted)

    elapsed = time.time() - t0
    print(f"\nPatching Complete in {elapsed:.2f}s:")
    print(f"  Files processed: {stats['total_files']}")
    print(f"  Files patched with Vietnamese: {stats['patched_files']}")
    print(f"  Total dialogue strings replaced: {stats['patched_strings']}")

    # 3. Repack lua.arcx
    output_lua_arcx = ROOT / "dist" / "lua_patched_vi.arcx"
    output_lua_arcx.parent.mkdir(parents=True, exist_ok=True)
    unpacked_dir = ROOT / "work" / "research" / "lua_full_unpacked"

    print(f"\nRepacking 2,833 entries into {output_lua_arcx}...")
    repack_archive(unpacked_dir, output_lua_arcx, encrypt_payload=False)
    arc = ArcxArchive(output_lua_arcx)
    print(f"Successfully created {output_lua_arcx} ({output_lua_arcx.stat().st_size} bytes, {len(arc.entries)} entries)!")

    # 4. Deploy to Steam and Yostar clients
    steam_lua = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Scripts\lua.arcx")
    yostar_lua = Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx")

    if steam_lua.parent.exists():
        shutil.copy2(output_lua_arcx, steam_lua)
        print(f"Deployed to Steam: {steam_lua} ({steam_lua.stat().st_size} bytes)")
    if yostar_lua.parent.exists():
        shutil.copy2(output_lua_arcx, yostar_lua)
        print(f"Deployed to Yostar: {yostar_lua} ({yostar_lua.stat().st_size} bytes)")

    print("\n=== LUA PATCHING & DEPLOYMENT FINISHED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
