#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 18 (Đợt 10 - FINAL CAMPAIGN OF ENTIRE GAME):
CG NPC Stories & CG Disc Stories:
- Partition A: CG NPC Stories (CG_npc133_01..02, CG_npc172_01..02, CG_npc173_01..02, CG_npc174_01..02) - 8 scenes
- Partition B: CG Disc Stories (CG_disc4004..4066) - 25 scenes
Total: 33 scenes, ~3,078 lines.
"""

import json
from pathlib import Path
import re
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from test_lua_roundtrip import Lua53Chunk
from translate_remaining_lua_avg import is_genuine_dialogue

CAMPAIGN_DIR = ROOT / "work/editorial/final_cg_npc_and_disc_editorial_20261025_r01"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

def is_tech_str(s: str) -> bool:
    return bool(
        s.startswith(('ep_', 'story_main_', 'qstory_', 'fx_avg_', 'Set', 'sys_', 'BGM_', 'SE_', 'white_room', 'EV_', 'desert_')) or
        ('_' in s and ' ' not in s and re.match(r'^[a-z0-9_]+$', s))
    )

def extract_bytecode_pairs(pr_en, pr_vi, sc, acc, path=""):
    for i, ((kt_en, v_en), (kt_vi, v_vi)) in enumerate(zip(pr_en['constants'], pr_vi['constants'])):
        if kt_en in (4, 20):
            try:
                s_en = v_en[1].decode('utf-8')
                s_vi = v_vi[1].decode('utf-8')
                if is_genuine_dialogue(s_en):
                    item_id = f"{sc}.{path}{i}"
                    tokens = TAG_PATTERN.findall(s_en)
                    acc.append({
                        "id": item_id,
                        "scene_id": sc,
                        "en": s_en,
                        "current_vi": s_vi,
                        "tokens": tokens,
                        "is_tech": is_tech_str(s_en)
                    })
            except:
                pass
    for j, (c_en, c_vi) in enumerate(zip(pr_en['protos'], pr_vi['protos'])):
        extract_bytecode_pairs(c_en, c_vi, sc, acc, path + f"p{j}_")

def main():
    print("Setting up Campaign 18 (FINAL CAMPAIGN) workspace...")

    mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
    pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
    arc = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

    npc_scenes = [
        'CG_npc133_01', 'CG_npc133_02',
        'CG_npc172_01', 'CG_npc172_02',
        'CG_npc173_01', 'CG_npc173_02',
        'CG_npc174_01', 'CG_npc174_02',
    ]

    disc_scenes = [
        'CG_disc4004', 'CG_disc4005', 'CG_disc4006', 'CG_disc4007', 'CG_disc4008',
        'CG_disc4015', 'CG_disc4016', 'CG_disc4017',
        'CG_disc4026', 'CG_disc4027', 'CG_disc4028', 'CG_disc4029',
        'CG_disc4036', 'CG_disc4037', 'CG_disc4038',
        'CG_disc4044', 'CG_disc4045', 'CG_disc4048',
        'CG_disc4051', 'CG_disc4054', 'CG_disc4055', 'CG_disc4057', 'CG_disc4059',
        'CG_disc4061', 'CG_disc4066'
    ]

    def extract_scene_list(scene_list):
        items = []
        for sc in scene_list:
            fname = f"{sc}.lua"
            if fname not in mapping:
                print(f"Warning: {fname} missing from mapping!")
                continue
            entry_info = mapping[fname]
            idx = entry_info['entry']['index']
            payload_en = arc.extract_entry(arc.entries[idx], raw_pristine)
            proto_en = Lua53Chunk(xxtea_decrypt(payload_en, XXTEA_KEY)[34:]).parse_proto()

            entry_file = entries_dir / entry_info['filename']
            proto_vi = Lua53Chunk(xxtea_decrypt(entry_file.read_bytes(), XXTEA_KEY)[34:]).parse_proto()

            acc = []
            extract_bytecode_pairs(proto_en, proto_vi, sc, acc)
            items.extend(acc)
        return items

    print("Extracting Partition A (CG NPC Stories)...")
    part_a = extract_scene_list(npc_scenes)
    print(f"Partition A: {len(part_a)} items across {len(npc_scenes)} scenes.")

    print("Extracting Partition B (CG Disc Stories)...")
    part_b = extract_scene_list(disc_scenes)
    print(f"Partition B: {len(part_b)} items across {len(disc_scenes)} scenes.")

    all_items = part_a + part_b
    print(f"Total Campaign 18 items: {len(all_items)} across {len(npc_scenes) + len(disc_scenes)} scenes.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(part_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(part_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_18_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    # Technical audit
    unclosed_a = [it['id'] for it in part_a if '<size=' in it['en'] and '</size>' not in it['en']]
    unclosed_b = [it['id'] for it in part_b if '<size=' in it['en'] and '</size>' not in it['en']]
    ctrls = [it['id'] for it in all_items if any(ord(c) < 32 and c not in '\t\r\n' for c in it['en'])]

    print(f"\n--- Technical Audit for Campaign 18 ---")
    print(f"Unclosed <size> in Part A: {len(unclosed_a)} -> {unclosed_a}")
    print(f"Unclosed <size> in Part B: {len(unclosed_b)} -> {unclosed_b}")
    print(f"Binary control characters in All: {len(ctrls)} -> {ctrls}")

    with open(CAMPAIGN_DIR / "CAMPAIGN_18_TECHNICAL_AUDIT.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_items": len(all_items),
            "partition_a_items": len(part_a),
            "partition_b_items": len(part_b),
            "unclosed_size_a": unclosed_a,
            "unclosed_size_b": unclosed_b,
            "ctrls": ctrls
        }, f, indent=2)

if __name__ == "__main__":
    main()
