#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 15 (Đợt 7):
Event Stories Part 3:
- STev_05 (Post Haste's Commission / Port Bellin Letters): 10 scenes, ~1,089 lines
- STev_07 (The Reunion in Emor / Igna's Commission): 9 scenes, ~977 lines
- STev_08 (Energy Crisis in Lucky Oasis / Bloc's Stall): 8 scenes, ~856 lines
Total: 27 scenes, ~2,922 lines.
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

CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01"
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
    print("Setting up Campaign 15 workspace...")

    mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
    pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
    arc = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

    target_scenes = [
        'STev_05_01', 'STev_05_02_a', 'STev_05_02_b', 'STev_05_02_c', 'STev_05_03', 'STev_05_04', 'STev_05_05', 'STev_05_06', 'STev_05_07', 'STev_05_08',
        'STev_07_01', 'STev_07_02', 'STev_07_03', 'STev_07_04', 'STev_07_05', 'STev_07_06', 'STev_07_07', 'STev_07_08', 'STev_07_09',
        'STev_08_01', 'STev_08_02', 'STev_08_03', 'STev_08_04', 'STev_08_05', 'STev_08_06', 'STev_08_07', 'STev_08_08'
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

    print(f"\nTotal Campaign 15 items: {len(all_items)} across {len(set(x['scene_id'] for x in all_items))} scenes.")

    # Partitioning:
    # Partition A: STev_05 (10 scenes) + STev_07_01..03 (3 scenes) = 13 scenes
    # Partition B: STev_07_04..09 (6 scenes) + STev_08 (8 scenes) = 14 scenes
    part_a_scenes = set([
        'STev_05_01', 'STev_05_02_a', 'STev_05_02_b', 'STev_05_02_c', 'STev_05_03', 'STev_05_04', 'STev_05_05', 'STev_05_06', 'STev_05_07', 'STev_05_08',
        'STev_07_01', 'STev_07_02', 'STev_07_03'
    ])

    items_a = [x for x in all_items if x['scene_id'] in part_a_scenes]
    items_b = [x for x in all_items if x['scene_id'] not in part_a_scenes]

    print(f"Partition A: {len(items_a)} items across {len(set(x['scene_id'] for x in items_a))} scenes.")
    print(f"Partition B: {len(items_b)} items across {len(set(x['scene_id'] for x in items_b))} scenes.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_15_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print("Campaign 15 workspace setup successfully initialized!")

if __name__ == "__main__":
    main()
