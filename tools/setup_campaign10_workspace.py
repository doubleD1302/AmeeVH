#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace and Partitions for Campaign 10 (Đợt 2):
Act 4 Final Climax Story (STm09_00_a to STm09_07_a, 2,923 lines across 21 scenes).
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
WORK_DIR = ROOT / "work/editorial/act4_final_story_editorial_20261024_r01"
WORK_DIR.mkdir(parents=True, exist_ok=True)

b4_en_path = ROOT / "work/batches/batch_10000_avg_clean_b4.json"
b4_vi_path = ROOT / "work/batches/batch_10k_b4_approved.json"

en_data = json.load(open(b4_en_path, encoding="utf-8"))
vi_data = json.load(open(b4_vi_path, encoding="utf-8"))

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

items = []
for k in en_data:
    if not k.startswith("STm09"):
        continue
    en_text = en_data[k]
    tokens = TAG_PATTERN.findall(en_text)
    sc = k.split(".")[0]
    
    is_tech = bool(
        en_text.startswith(('ep_', 'story_main_', 'qstory_main_', 'fx_avg_', 'Set', 'sys_', 'BGM_', 'SE_', 'white_room', 'EV_', 'desert_')) or
        ('_' in en_text and ' ' not in en_text and re.match(r'^[a-z0-9_]+$', en_text))
    )
    
    items.append({
        "id": k,
        "scene_id": sc,
        "en": en_text,
        "current_vi": vi_data.get(k, ""),
        "tokens": tokens,
        "is_tech": is_tech
    })

print(f"Total extracted items for STm09: {len(items)}")

part_a_scenes = {
    'STm09_00_a', 'STm09_00_b', 'STm09_01_a', 'STm09_01_b', 'STm09_01_c',
    'STm09_01_d', 'STm09_02_a', 'STm09_02_b', 'STm09_02_c', 'STm09_03_a'
}

items_a = [x for x in items if x["scene_id"] in part_a_scenes]
items_b = [x for x in items if x["scene_id"] not in part_a_scenes]

scenes_a = sorted(list(set(x["scene_id"] for x in items_a)))
scenes_b = sorted(list(set(x["scene_id"] for x in items_b)))

print(f"Partition A: {len(items_a)} items across {len(scenes_a)} scenes: {scenes_a}")
print(f"Partition B: {len(items_b)} items across {len(scenes_b)} scenes: {scenes_b}")

with open(WORK_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_a, f, ensure_ascii=False, indent=2)

with open(WORK_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_b, f, ensure_ascii=False, indent=2)

print("Setup Campaign 10 completed successfully!")
