#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 16 (Đợt 8):
Event Stories Part 4 (FINAL EVENT STORIES IN GAME):
- STev_09 (Mirage Desert Expedition): 8 scenes, 764 lines
- STev_10 (Vacation Time with Willow): 9 scenes, 913 lines
- STev_11 (Monolith at Sea with Leafia): 9 scenes, 858 lines
- STev_12 (Tea Party with Eleanor & Friends): 9 scenes, 906 lines
Total: 35 scenes, 3,441 lines.
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

CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01"
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
    print("Setting up Campaign 16 workspace...")

    mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
    pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
    arc = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

    target_scenes = [
        'STev_09_01', 'STev_09_02', 'STev_09_03', 'STev_09_04', 'STev_09_05', 'STev_09_06', 'STev_09_07', 'STev_09_08',
        'STev_10_01', 'STev_10_02', 'STev_10_03', 'STev_10_04', 'STev_10_05', 'STev_10_06', 'STev_10_07', 'STev_10_08', 'STev_10_09',
        'STev_11_01', 'STev_11_02', 'STev_11_03', 'STev_11_04', 'STev_11_05', 'STev_11_06', 'STev_11_07', 'STev_11_08', 'STev_11_09',
        'STev_12_01', 'STev_12_02', 'STev_12_03', 'STev_12_04', 'STev_12_05', 'STev_12_06', 'STev_12_07', 'STev_12_08', 'STev_12_09'
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

    print(f"\nTotal Campaign 16 items: {len(all_items)} across {len(set(x['scene_id'] for x in all_items))} scenes.")

    # Partitioning:
    # Partition A: STev_09 (8 scenes) + STev_10 (9 scenes) = 17 scenes
    # Partition B: STev_11 (9 scenes) + STev_12 (9 scenes) = 18 scenes
    part_a_scenes = set([
        'STev_09_01', 'STev_09_02', 'STev_09_03', 'STev_09_04', 'STev_09_05', 'STev_09_06', 'STev_09_07', 'STev_09_08',
        'STev_10_01', 'STev_10_02', 'STev_10_03', 'STev_10_04', 'STev_10_05', 'STev_10_06', 'STev_10_07', 'STev_10_08', 'STev_10_09'
    ])

    items_a = [x for x in all_items if x['scene_id'] in part_a_scenes]
    items_b = [x for x in all_items if x['scene_id'] not in part_a_scenes]

    print(f"Partition A: {len(items_a)} items across {len(set(x['scene_id'] for x in items_a))} scenes.")
    print(f"Partition B: {len(items_b)} items across {len(set(x['scene_id'] for x in items_b))} scenes.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_16_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print("Campaign 16 workspace setup successfully initialized!")

if __name__ == "__main__":
    main()
