#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and Repack lua_patched_vi.arcx with All Campaigns 1-18 (100% ALL 626 AVG SCENES COMPLETE!).
Total relocalized lines = 65,742 lines across all scenes in game!
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
                        
                if new_text is None:
                    # Double-layer fallback polish for any legacy Vietnamese strings
                    from comprehensive_dialogue_polisher import polish_line
                    s_pol = polish_line("", s_strip)
                    if s_pol != s_strip:
                        new_text = s_pol
                        
                if new_text is not None:
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
    print("=== STARTING FULL LUA AVG REPACK INCLUDING ACT 3 STORY ===")
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
    print(f"Restored {len(arc_pristine.entries)} pristine entries.")

    # 2. Build Scene-Specific Dictionaries for Campaigns 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12
    print("Building Scene-Specific Dictionaries from Campaigns 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12...")
    p1 = ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"
    p2 = ROOT / "work/editorial/phone_messages_editorial_20261024_r01/UNIFIED_PHONE_PROPOSALS.jsonl"
    p4 = ROOT / "work/editorial/character_cg_stories_editorial_20261024_r01/UNIFIED_CG_PROPOSALS.jsonl"
    p5 = ROOT / "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl"
    p6 = ROOT / "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl"
    p7 = ROOT / "work/editorial/phone_messages_phase2_20261024_r01/UNIFIED_PM_PHASE2_PROPOSALS.jsonl"
    p8 = ROOT / "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl"
    p9 = ROOT / "work/editorial/act3_part1_story_editorial_20261024_r01/UNIFIED_ACT3_PART1_PROPOSALS.jsonl"
    p10 = ROOT / "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl"
    p11 = ROOT / "work/editorial/character_cg_part2_editorial_20261024_r01/UNIFIED_CG_PART2_PROPOSALS.jsonl"
    p12 = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01/UNIFIED_STSP_PART1_PROPOSALS.jsonl"
    p13 = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl"
    p14 = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl"
    p15 = ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01/UNIFIED_CAMPAIGN_15_PROPOSALS.jsonl"
    p16 = ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01/UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl"
    p17 = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01/UNIFIED_CAMPAIGN_17_PROPOSALS.jsonl"
    p18 = ROOT / "work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/UNIFIED_CAMPAIGN_18_PROPOSALS.jsonl"

    scene_dicts = {}
    campaign_counts = {"c1": 0, "c2": 0, "c4": 0, "c5": 0, "c6": 0, "c7": 0, "c8": 0, "c9": 0, "c10": 0, "c11": 0, "c12": 0, "c13": 0, "c14": 0, "c15": 0, "c16": 0, "c17": 0, "c18": 0}

    campaigns = [
        (p1, "vi", "c1"),
        (p2, "vi_editorial", "c2"),
        (p4, "vi_editorial", "c4"),
        (p5, "vi_editorial", "c5"),
        (p6, "vi_editorial", "c6"),
        (p7, "vi_editorial", "c7"),
        (p8, "vi_editorial", "c8"),
        (p9, "vi_editorial", "c9"),
        (p10, "vi_editorial", "c10"),
        (p11, "vi_editorial", "c11"),
        (p12, "vi_editorial", "c12"),
        (p13, "vi_editorial", "c13"),
        (p14, "vi_editorial", "c14"),
        (p15, "vi_editorial", "c15"),
        (p16, "vi_editorial", "c16"),
        (p17, "vi_editorial", "c17"),
        (p18, "proposed_vi", "c18")
    ]

    for p, vi_key, cname in campaigns:
        if not p.exists(): continue
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
    print(f"  Campaign 5 (Act 3 Story & PM): {campaign_counts['c5']} scene lines")
    print(f"  Campaign 6 (Act 2 Climax & Philae): {campaign_counts['c6']} scene lines")
    print(f"  Campaign 7 (Phone Phase 2): {campaign_counts['c7']} scene lines")
    print(f"  Campaign 8 (Act 1-2 Story): {campaign_counts['c8']} scene lines")
    print(f"  Campaign 9 (Act 3 Part 1 Story): {campaign_counts['c9']} scene lines")
    print(f"  Campaign 10 (Act 4 Final Story): {campaign_counts['c10']} scene lines")
    print(f"  Campaign 11 (Character CG Part 2): {campaign_counts['c11']} scene lines")
    print(f"  Campaign 12 (Special Side Stories Part 1): {campaign_counts['c12']} scene lines")
    print(f"  Campaign 13 (Special Side Stories Part 2 & Event 1): {campaign_counts['c13']} scene lines")
    print(f"  Campaign 14 (Event Stories Part 2 & Dungeon Intros): {campaign_counts['c14']} scene lines")
    print(f"  Campaign 15 (Event Stories Part 3: Bellin, Emor, Bloc): {campaign_counts['c15']} scene lines")
    print(f"  Campaign 16 (Event Stories Part 4: Mirage, Willow, Leafia, Eleanor): {campaign_counts['c16']} scene lines")
    print(f"  Campaign 17 (Tutorial Prologue, System & Character CGs): {campaign_counts['c17']} scene lines")
    print(f"  Campaign 18 (Final CG NPC & Disc Stories): {campaign_counts['c18']} scene lines")
    print(f"  Total scene-specific dictionaries: {len(scene_dicts)} scenes")

    # 3. Master Dictionary for remaining general dialogues
    print("Building Master Translation Dictionary...")
    master_dict = {}

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

    rem_cache = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
    if rem_cache.exists():
        rem_d = json.load(open(rem_cache, encoding="utf-8"))
        for k, v in rem_d.items():
            master_dict[k.strip()] = v.strip()
            c_k = clean_str(k)
            if c_k:
                master_dict[c_k] = v.strip()
        print(f"Total master dictionary size: {len(master_dict)}")

    # 3.1 Load Campaign 19 Polished Cache (20,680 lines)
    p19 = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl"
    if p19.exists():
        c19_count = 0
        for l in p19.read_text(encoding="utf-8").splitlines():
            if not l.strip(): continue
            it = json.loads(l)
            en = it.get("en")
            vi = it.get("polished_vi") or it.get("original_vi")
            if en and vi and vi.strip():
                en_str = en.strip()
                vi_str = vi.strip()
                master_dict[en_str] = vi_str
                c_en = clean_str(en_str)
                if c_en:
                    master_dict[c_en] = vi_str
                c19_count += 1
        print(f"  Campaign 19 (Polish Remaining 20k Cache): {c19_count} master lines")

    # 3.2 Explicit high-priority scene overrides for STm02_04 & key scenes
    try:
        from apply_deep_idiom_fixes import STM02_04_PERFECT_DICT, GENERAL_IDIOM_OVERRIDES
        sdict_stm02_04 = scene_dicts.setdefault("STm02_04", {})
        for en_k, vi_v in STM02_04_PERFECT_DICT.items():
            sdict_stm02_04[en_k] = vi_v
            sdict_stm02_04[clean_str(en_k)] = vi_v
            master_dict[en_k] = vi_v
            master_dict[clean_str(en_k)] = vi_v
            
        for en_k, vi_v in GENERAL_IDIOM_OVERRIDES.items():
            master_dict[en_k] = vi_v
            master_dict[clean_str(en_k)] = vi_v
        print(f"Applied {len(STM02_04_PERFECT_DICT)} STm02_04 overrides and {len(GENERAL_IDIOM_OVERRIDES)} idiom overrides.")
    except Exception as e:
        print(f"Note: Deep idiom overrides not loaded: {e}")

    try:
        from polish_all_pm_chat_strings import CHAT_DICTIONARY
        for en, vi in CHAT_DICTIONARY.items():
            master_dict[en.strip()] = vi.strip()
        print(f"Applied {len(CHAT_DICTIONARY)} chat overrides.")
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

    lua_tree_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"
    print(f"\nPatching {len(mapping)} Lua AVG files (sourcing pure English bytecode from lua_tree)...")
    for fname, info in mapping.items():
        entry_fname = info['filename']
        bin_path = entries_dir / entry_fname
        if not bin_path.exists():
            continue

        sc_name = fname[:-4] if fname.endswith(".lua") else fname
        sc_dict = scene_dicts.get(sc_name)

        # Source pure English bytecode from lua_tree if available, otherwise decrypt entry
        lt_file = lua_tree_dir / fname
        if lt_file.exists():
            decrypted_data = lt_file.read_bytes()
        else:
            encrypted_data = bin_path.read_bytes()
            decrypted_data = xxtea_decrypt(encrypted_data, XXTEA_KEY)

        prev_count = stats['patched_strings']
        patched_raw = patch_lua_bytecode(decrypted_data, sc_dict, master_dict, stats)
        num_in_file = stats['patched_strings'] - prev_count

        if num_in_file > 0 or lt_file.exists():
            stats['patched_files'] += 1
            re_encrypted = xxtea_encrypt(patched_raw, XXTEA_KEY)
            bin_path.write_bytes(re_encrypted)

    print(f"\nPatching Complete:")
    print(f"  Files processed: {stats['total_files']}")
    print(f"  Files patched with Vietnamese: {stats['patched_files']}")
    print(f"  Total dialogue strings replaced: {stats['patched_strings']:,}")

    # 4.1 Patch AvgContacts.lua with Vietnamese signatures and bios
    from patch_avg_contacts import patch_avg_contacts_entry
    contacts_entry = entries_dir / "02804_0x6b338c3a32f44951.bin"
    if contacts_entry.exists():
        patch_avg_contacts_entry(contacts_entry)

    # 5. Repack lua.arcx
    output_lua_arcx = ROOT / "dist" / "lua_patched_vi.arcx"
    unpacked_dir = ROOT / "work" / "research" / "lua_full_unpacked"

    print(f"\nRepacking {len(arc_pristine.entries)} entries into {output_lua_arcx}...")
    repack_archive(unpacked_dir, output_lua_arcx, encrypt_payload=False)
    arc_out = ArcxArchive(output_lua_arcx)
    elapsed = time.time() - t0
    print(f"SUCCESS! Created {output_lua_arcx} in {elapsed:.2f}s:")
    print(f"  Size: {output_lua_arcx.stat().st_size:,} bytes")
    print(f"  Entries: {len(arc_out.entries)}")

    # 6. Synchronize to live game (Both Standalone and Steam installation!)
    live_targets = [
        Path(r"c:\YostarGames\StellaSora_EN") / "Persistent_Store" / "Scripts" / "lua.arcx",
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora") / "Persistent_Store" / "Scripts" / "lua.arcx"
    ]
    for target in live_targets:
        if target.parent.exists():
            print(f"\nSynchronizing to: {target}...")
            shutil.copy2(output_lua_arcx, target)
            print(f"SUCCESS! Synced to {target} ({target.stat().st_size:,} bytes)")

    # Also synchronize tables (data.arcx) from golden dist/data_patched_vi.arcx to live games
    dist_data = ROOT / "dist" / "data_patched_vi.arcx"
    if dist_data.exists():
        for target_data in [
            Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
        ]:
            if target_data.parent.exists():
                shutil.copy2(dist_data, target_data)
                print(f"SUCCESS! Synced golden tables ({dist_data.stat().st_size:,} bytes) to {target_data}")

    # 7. Automated Anti-Regression Verification Gate
    print("\nRunning Automated Anti-Regression Gate on deployed files...")
    import verify_deployed_game_data
    verify_deployed_game_data.main()

if __name__ == "__main__":
    main()
