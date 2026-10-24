#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 17 (Đợt 9):
Tutorial Prologue, System Stories & Final Character Stories:
- Non-CG scenes (STm10001, STm00, ST_sys, BBm, DP_single162, GD_gacha): 19 scenes, 1,257 lines
- CG Character stories (CG_149, CG_155, CG_156, CG_157, CG_158, CG_159, CG_160, CG_162): 22 scenes, 2,011 lines
Total: 41 scenes, 3,268 lines.
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

CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

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
    print("Setting up Campaign 17 workspace...")

    mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
    pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
    arc = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

    target_scenes = [
        # Non-CG (19 scenes)
        'STm10001_01', 'STm10001_02', 'STm10001_03', 'STm10001_04', 'STm10001_05',
        'STm10001_06', 'STm10001_07', 'STm10001_08', 'STm10001_09',
        'STm00_01', 'STm00_02',
        'ST_sys_reengagement', 'ST_sys_soldier_intro',
        'BBm10001_BT01', 'BBm_DormApproach', 'BBm_DormIndoor', 'BBm_DormOutdoor',
        'DP_single162', 'GD_gacha',
        # CG Character stories (22 scenes)
        'CG_149_01', 'CG_149_02', 'CG_149_03',
        'CG_155_03',
        'CG_156_01', 'CG_156_02', 'CG_156_03',
        'CG_157_01', 'CG_157_02', 'CG_157_03',
        'CG_158_01', 'CG_158_02', 'CG_158_03',
        'CG_159_01', 'CG_159_02', 'CG_159_03',
        'CG_160_01', 'CG_160_02', 'CG_160_03',
        'CG_162_01', 'CG_162_02', 'CG_162_03',
    ]

    all_items = []
    for sc in target_scenes:
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
        all_items.extend(acc)
        print(f"  {sc}: {len(acc)} dialogue items")

    print(f"\nTotal Campaign 17 items: {len(all_items)} across {len(set(x['scene_id'] for x in all_items))} scenes.")

    # Partitioning:
    # Partition A: Non-CG (19 scenes) + CG_149 (3 scenes) = 22 scenes
    # Partition B: CG_155 to CG_162 (19 scenes) = 19 scenes
    part_a_scenes = set([
        'STm10001_01', 'STm10001_02', 'STm10001_03', 'STm10001_04', 'STm10001_05',
        'STm10001_06', 'STm10001_07', 'STm10001_08', 'STm10001_09',
        'STm00_01', 'STm00_02',
        'ST_sys_reengagement', 'ST_sys_soldier_intro',
        'BBm10001_BT01', 'BBm_DormApproach', 'BBm_DormIndoor', 'BBm_DormOutdoor',
        'DP_single162', 'GD_gacha',
        'CG_149_01', 'CG_149_02', 'CG_149_03'
    ])

    items_a = [x for x in all_items if x['scene_id'] in part_a_scenes]
    items_b = [x for x in all_items if x['scene_id'] not in part_a_scenes]

    print(f"Partition A: {len(items_a)} items across {len(set(x['scene_id'] for x in items_a))} scenes.")
    print(f"Partition B: {len(items_b)} items across {len(set(x['scene_id'] for x in items_b))} scenes.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_17_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print("Campaign 17 workspace setup successfully initialized!")

if __name__ == "__main__":
    main()
