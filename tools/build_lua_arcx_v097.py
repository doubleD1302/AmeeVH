#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and Repack lua_patched_vi.arcx for Client v0.9.7.
Applies all 12,554 Lua story & dialogue lines:
- Campaign 1 (Story scenes): 4,550 lines
- Campaign 2 (Phone message scenes): 3,280 lines
- Campaign 4 (18 Heroines CG story scenes): 4,724 lines
- Batches 1-4 & Handcrafted Chat Dictionary (30,000+ general AVG lines)
Restores from pristine test_lua_full.arcx to ensure zero MT remnants.
Repacks into dist/lua_patched_vi.arcx.
"""

import json
from pathlib import Path
import re
import shutil
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto
from arcx_adapter import xxtea_decrypt, xxtea_encrypt, XXTEA_KEY, repack_archive, ArcxArchive

def clean_str(s: str) -> str:
    """Strips control chars and whitespace."""
    return re.sub(r'^[\x00-\x1f]+', '', s).strip()

def patch_proto_constants(proto: dict, scene_dict: dict, master_dict: dict, stats: dict):
    new_constants = []
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                s_strip = s.strip()
                s_clean = clean_str(s)
                
                new_text = None
                if scene_dict:
                    if s_strip in scene_dict:
                        new_text = scene_dict[s_strip]
                    elif s_clean in scene_dict:
                        new_text = scene_dict[s_clean]
                        
                if new_text is None:
                    if s_strip in master_dict:
                        new_text = master_dict[s_strip]
                    elif s_clean in master_dict:
                        new_text = master_dict[s_clean]
                        
                if new_text is not None:
                    # Clean any accidental control char prefix in translation
                    new_text = clean_str(new_text)
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
        patch_proto_constants(child, scene_dict, master_dict, stats)

def patch_lua_bytecode(raw_decrypted: bytes, scene_dict: dict, master_dict: dict, stats: dict) -> bytes:
    chunk = Lua53Chunk(raw_decrypted)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()

    patch_proto_constants(proto, scene_dict, master_dict, stats)

    rebuilt_raw = hdr + bytes([size_up]) + serialize_proto(proto)
    return rebuilt_raw

def main():
    print("=== STARTING FULL LUA AVG REPACK FOR v0.9.7 ===")
    t0 = time.time()

    # 1. Restore entries from pristine test_lua_full.arcx
    entries_dir = ROOT / "work" / "research" / "lua_full_unpacked" / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    pristine_arcx = ROOT / "work" / "research" / "test_lua_full.arcx"
    print(f"Restoring pristine entries from {pristine_arcx.name}...")
    arc_pristine = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    for entry in arc_pristine.entries:
        fname = f"{entry['index']:05d}_{entry['hash_hex']}.bin"
        payload = arc_pristine.extract_entry(entry, raw_pristine)
        (entries_dir / fname).write_bytes(payload)
    print(f"Restored {len(arc_pristine.entries)} pristine entries into {entries_dir}")

    # 2. Build Scene-Specific Dictionaries for Campaigns 1, 2, 4
    print("Building Scene-Specific Dictionaries from Campaigns 1, 2, 4...")
    p1 = ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"
    p2 = ROOT / "work/editorial/phone_messages_editorial_20261024_r01/UNIFIED_PHONE_PROPOSALS.jsonl"
    p4 = ROOT / "work/editorial/character_cg_stories_editorial_20261024_r01/UNIFIED_CG_PROPOSALS.jsonl"

    scene_dicts = {}
    campaign_counts = {"c1": 0, "c2": 0, "c4": 0}

    for p, vi_key, cname in [(p1, "vi", "c1"), (p2, "vi_editorial", "c2"), (p4, "vi_editorial", "c4")]:
        for l in p.read_text(encoding="utf-8").splitlines():
            if not l.strip(): continue
            it = json.loads(l)
            if it.get("is_tech"): continue
            sid = it.get("id") or ""
            sc = it.get("scene_id") or sid.split(".")[0]
            en = it.get("en")
            vi = it.get(vi_key)
            if en and vi and vi.strip():
                en_str = en.strip()
                vi_str = vi.strip()
                sdict = scene_dicts.setdefault(sc, {})
                sdict[en_str] = vi_str
                c_en = clean_str(en_str)
                if c_en:
                    sdict[c_en] = vi_str
                campaign_counts[cname] += 1

    print(f"  Campaign 1 (Story): {campaign_counts['c1']} scene lines")
    print(f"  Campaign 2 (Phone): {campaign_counts['c2']} scene lines")
    print(f"  Campaign 4 (CG): {campaign_counts['c4']} scene lines")
    print(f"  Total scene-specific dictionaries: {len(scene_dicts)} scenes")

    # 3. Build Master Dictionary for fallback
    print("Building Master Translation Dictionary for all remaining lines...")
    master_dict = {}

    # Source A: Pristine Batches 1-4 paired with current approved batches
    batches_en = [
        "batch_10000_avg_clean.json", "batch_10000_avg_clean_b2.json",
        "batch_10000_avg_clean_b3.json", "batch_10000_avg_clean_b4.json"
    ]
    batches_vi = [
        "batch_10k_approved.json", "batch_10k_b2_approved.json",
        "batch_10k_b3_approved.json", "batch_10k_b4_approved.json"
    ]
    for en_f, vi_f in zip(batches_en, batches_vi):
        en_p = ROOT / "work" / "batches_backup_pre_lightnovel" / en_f
        if not en_p.exists():
            en_p = ROOT / "work" / "batches" / en_f
        vi_p = ROOT / "work" / "batches" / vi_f
        if en_p.exists() and vi_p.exists():
            en_d = json.load(open(en_p, encoding="utf-8"))
            vi_d = json.load(open(vi_p, encoding="utf-8"))
            for k, en in en_d.items():
                if k in vi_d:
                    en_str = en.strip()
                    vi_str = vi_d[k].strip()
                    master_dict[en_str] = vi_str
                    c_en = clean_str(en_str)
                    if c_en:
                        master_dict[c_en] = vi_str

    print(f"Loaded {len(master_dict)} items from batches 1-4.")

    # Source B: Remaining translated dialogue
    rem_cache = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
    if rem_cache.exists():
        rem_d = json.load(open(rem_cache, encoding="utf-8"))
        for k, v in rem_d.items():
            master_dict[k.strip()] = v.strip()
            c_k = clean_str(k)
            if c_k:
                master_dict[c_k] = v.strip()
        print(f"Total master dictionary size after remaining dialogue: {len(master_dict)}")

    # Source C: Handcrafted Chat Dictionary
    try:
        from polish_all_pm_chat_strings import CHAT_DICTIONARY
        for en, vi in CHAT_DICTIONARY.items():
            master_dict[en.strip()] = vi.strip()
        print(f"Applied {len(CHAT_DICTIONARY)} chat overrides to master dictionary.")
    except Exception as e:
        print(f"Note: CHAT_DICTIONARY not loaded: {e}")

    # 4. Patch all 626 Lua AVG files
    mapping_path = ROOT / "work" / "research" / "avg_file_to_entry.json"
    mapping = json.load(open(mapping_path, encoding="utf-8"))

    stats = {
        'total_files': len(mapping),
        'patched_files': 0,
        'patched_strings': 0
    }

    print(f"\nPatching {len(mapping)} Lua AVG files...")
    for fname, info in mapping.items():
        entry_fname = info['filename']
        bin_path = entries_dir / entry_fname
        if not bin_path.exists():
            continue

        sc_name = fname[:-4] if fname.endswith(".lua") else fname
        sc_dict = scene_dicts.get(sc_name)

        encrypted_data = bin_path.read_bytes()
        decrypted_data = xxtea_decrypt(encrypted_data, XXTEA_KEY)

        prev_count = stats['patched_strings']
        patched_raw = patch_lua_bytecode(decrypted_data, sc_dict, master_dict, stats)
        num_in_file = stats['patched_strings'] - prev_count

        if num_in_file > 0:
            stats['patched_files'] += 1
            re_encrypted = xxtea_encrypt(patched_raw, XXTEA_KEY)
            bin_path.write_bytes(re_encrypted)

    print(f"\nPatching Complete:")
    print(f"  Files processed: {stats['total_files']}")
    print(f"  Files patched with Vietnamese: {stats['patched_files']}")
    print(f"  Total dialogue strings replaced: {stats['patched_strings']:,}")

    # 5. Repack lua.arcx
    output_lua_arcx = ROOT / "dist" / "lua_patched_vi.arcx"
    output_lua_arcx.parent.mkdir(parents=True, exist_ok=True)
    unpacked_dir = ROOT / "work" / "research" / "lua_full_unpacked"

    print(f"\nRepacking {len(arc_pristine.entries)} entries into {output_lua_arcx}...")
    repack_archive(unpacked_dir, output_lua_arcx, encrypt_payload=False)
    arc_out = ArcxArchive(output_lua_arcx)
    elapsed = time.time() - t0
    print(f"SUCCESS! Created {output_lua_arcx} in {elapsed:.2f}s:")
    print(f"  Size: {output_lua_arcx.stat().st_size:,} bytes")
    print(f"  Entries: {len(arc_out.entries)}")

if __name__ == "__main__":
    main()
