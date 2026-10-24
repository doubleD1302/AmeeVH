#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 14 (Đợt 6):
Event Stories Part 2 & Dungeon Intros:
- DP_* (Dungeon & Daily Intros): 18 scenes, 305 lines
- STev_02 (Echoes / Mirage of Stars Complete): 13 scenes, 1,008 lines (01-06 from b4, 07-11 from pristine bytecode)
- STev_03 (Cangwu Festival of Loong Complete): 9 scenes, 843 lines (from pristine bytecode)
- STev_04 (Golden Sands / Desert Complete): 10 scenes, 1,057 lines (from pristine bytecode)
Total: 50 scenes, ~3,213 lines.
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

CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

b4_en_path = ROOT / "work/batches/batch_10000_avg_clean_b4.json"
b4_vi_path = ROOT / "work/batches/batch_10k_b4_approved.json"

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
    print("Setting up Campaign 14 workspace...")
    b4_en = json.load(open(b4_en_path, encoding="utf-8"))
    b4_vi = json.load(open(b4_vi_path, encoding="utf-8"))

    mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
    pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
    arc = ArcxArchive(pristine_arcx)
    raw_pristine = pristine_arcx.read_bytes()
    entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

    # Part 1: B4 items (DP_* and STev_02_01 to STev_02_06)
    b4_items = []
    for k, en_text in b4_en.items():
        sc = k.split(".")[0]
        if sc.startswith("DP_") or (sc.startswith("STev_02_") and sc in [
            'STev_02_01', 'STev_02_02', 'STev_02_03', 'STev_02_04_a', 'STev_02_04_b', 'STev_02_04_c', 'STev_02_05', 'STev_02_06'
        ]):
            tokens = TAG_PATTERN.findall(en_text)
            b4_items.append({
                "id": k,
                "scene_id": sc,
                "en": en_text,
                "current_vi": b4_vi.get(k, ""),
                "tokens": tokens,
                "is_tech": is_tech_str(en_text)
            })

    print(f"Loaded {len(b4_items)} items from Batch 4.")

    # Part 2: Bytecode items (STev_02_07 to STev_02_11, STev_03, STev_04)
    bytecode_scenes = [
        'STev_02_07', 'STev_02_08', 'STev_02_09', 'STev_02_10', 'STev_02_11',
        'STev_03_01', 'STev_03_02', 'STev_03_03', 'STev_03_04', 'STev_03_05', 'STev_03_06', 'STev_03_07', 'STev_03_08', 'STev_03_09',
        'STev_04_01', 'STev_04_02', 'STev_04_03', 'STev_04_04', 'STev_04_05', 'STev_04_06', 'STev_04_07', 'STev_04_08', 'STev_04_09', 'STev_04_10'
    ]

    bytecode_items = []
    for sc in bytecode_scenes:
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
        bytecode_items.extend(acc)
        print(f"  {sc}: {len(acc)} dialogue items")

    print(f"Loaded {len(bytecode_items)} items from bytecode.")
    all_items = b4_items + bytecode_items
    print(f"Total Campaign 14 items: {len(all_items)} across {len(set(x['scene_id'] for x in all_items))} scenes.")

    # Partitioning:
    # Partition A: DP_* (305) + STev_02 (1,008) + STev_03_01..03 (282) = ~1,595 items
    # Partition B: STev_03_04..09 (561) + STev_04 (1,057) = ~1,618 items
    part_a_scenes = set([x['scene_id'] for x in b4_items if x['scene_id'].startswith(('DP_', 'STev_02_'))] + [
        'STev_02_07', 'STev_02_08', 'STev_02_09', 'STev_02_10', 'STev_02_11',
        'STev_03_01', 'STev_03_02', 'STev_03_03'
    ])

    items_a = [x for x in all_items if x['scene_id'] in part_a_scenes]
    items_b = [x for x in all_items if x['scene_id'] not in part_a_scenes]

    print(f"Partition A: {len(items_a)} items across {len(set(x['scene_id'] for x in items_a))} scenes.")
    print(f"Partition B: {len(items_b)} items across {len(set(x['scene_id'] for x in items_b))} scenes.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_14_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print("Campaign 14 workspace setup successfully initialized!")

if __name__ == "__main__":
    main()
