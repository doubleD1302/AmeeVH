#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace and Partitions for Campaign 12 (Đợt 4):
Special Side Stories Part 1 (STsp_01 to STsp_11, 34 scenes, 2,936 lines).
- Partition A: STsp_01 to STsp_05 (16 scenes, 1,394 lines)
  Stories: Chitose Sword Journey, Desert Aftermath, Cangwu Blossoms (Jinglin/Shimiao/Chixia), Goodwind Matcha Dreaming, Office Expense Shenanigans
- Partition B: STsp_06 to STsp_11 (18 scenes, 1,542 lines)
  Stories: Imperial Guard Promo (Tilia), Snowish Festival (Freesia/Teresa), Dusk Arbiter Prison, Mistique Partner, Ridge Harvest, Donna Sunlight
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
WORK_DIR = ROOT / "work" / "editorial" / "side_stories_part1_editorial_20261025_r01"
WORK_DIR.mkdir(parents=True, exist_ok=True)

b4_en_path = ROOT / "work/batches/batch_10000_avg_clean_b4.json"
b4_vi_path = ROOT / "work/batches/batch_10k_b4_approved.json"

en_data = json.load(open(b4_en_path, encoding="utf-8"))
vi_data = json.load(open(b4_vi_path, encoding="utf-8"))

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

part_a_prefixes = ['STsp_01', 'STsp_02', 'STsp_03', 'STsp_04', 'STsp_05']
part_b_prefixes = ['STsp_06', 'STsp_07', 'STsp_08', 'STsp_09', 'STsp_10', 'STsp_11']

items_a = []
items_b = []

for k, en_text in en_data.items():
    sc = k.split(".")[0]
    prefix = sc[:7]
    
    tokens = TAG_PATTERN.findall(en_text)
    is_tech = bool(
        en_text.startswith(('ep_', 'story_main_', 'qstory_', 'fx_avg_', 'Set', 'sys_', 'BGM_', 'SE_', 'white_room', 'EV_', 'desert_')) or
        ('_' in en_text and ' ' not in en_text and re.match(r'^[a-z0-9_]+$', en_text))
    )
    
    entry = {
        "id": k,
        "scene_id": sc,
        "en": en_text,
        "current_vi": vi_data.get(k, ""),
        "tokens": tokens,
        "is_tech": is_tech
    }
    
    if prefix in part_a_prefixes:
        items_a.append(entry)
    elif prefix in part_b_prefixes:
        items_b.append(entry)

# Write JSONL
with open(WORK_DIR / "PARTITION_STSP_PART1_A.jsonl", "w", encoding="utf-8") as f:
    for item in items_a:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

with open(WORK_DIR / "PARTITION_STSP_PART1_B.jsonl", "w", encoding="utf-8") as f:
    for item in items_b:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# Write JSON arrays for source reference
with open(WORK_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_a, f, ensure_ascii=False, indent=2)

with open(WORK_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_b, f, ensure_ascii=False, indent=2)

print(f"Setup Complete for Campaign 12 (Đợt 4):")
print(f"  Partition A (STsp_01..05): {len(items_a)} lines across {len(set(x['scene_id'] for x in items_a))} scenes")
print(f"  Partition B (STsp_06..11): {len(items_b)} lines across {len(set(x['scene_id'] for x in items_b))} scenes")
print(f"  Total Campaign 12 Lines: {len(items_a) + len(items_b)}")
