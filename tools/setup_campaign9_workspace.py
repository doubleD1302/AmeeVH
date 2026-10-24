#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace and Partitions for Campaign 9:
Act 3 Part 1 Story (STm07_03 to STm08_09, 3,333 lines across 30 scenes).
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
WORK_DIR = ROOT / "work/editorial/act3_part1_story_editorial_20261024_r01"
WORK_DIR.mkdir(parents=True, exist_ok=True)

b3_en_path = ROOT / "work/batches/batch_10000_avg_clean_b3.json"
b3_vi_path = ROOT / "work/batches/batch_10k_b3_partB.json"

en_data = json.load(open(b3_en_path, encoding="utf-8"))
vi_data = json.load(open(b3_vi_path, encoding="utf-8"))

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

items = []
for k in vi_data:
    en_text = en_data.get(k, "")
    tokens = TAG_PATTERN.findall(en_text)
    sc = k.split(".")[0]
    
    is_tech = bool(
        en_text.startswith(('ep_', 'story_main_', 'qstory_main_', 'fx_avg_', 'Set', 'sys_', 'BGM_', 'SE_', 'white_room', 'EV_', 'forest_')) or
        ('_' in en_text and ' ' not in en_text and re.match(r'^[a-z0-9_]+$', en_text))
    )
    
    items.append({
        "id": k,
        "scene_id": sc,
        "en": en_text,
        "current_vi": vi_data[k],
        "tokens": tokens,
        "is_tech": is_tech
    })

print(f"Total extracted items: {len(items)}")

part_a_scenes = {
    'STm07_02', 'STm07_03', 'STm07_04', 'STm07_05_a', 'STm07_05_b', 'STm07_05_c',
    'STm07_06_a', 'STm07_06_ba', 'STm07_06_bb', 'STm07_06_bc', 'STm07_07', 'STm07_08', 'STm07_09'
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

align_src = ROOT / "work/editorial/act3_part1_prep_20261024_r01/ACT3_PART1_SCENE_ALIGNMENT.json"
align_dst = WORK_DIR / "ACT3_PART1_SCENE_ALIGNMENT.json"
if align_src.exists():
    align_dst.write_text(align_src.read_text(encoding="utf-8"), encoding="utf-8")
    print("Copied ACT3_PART1_SCENE_ALIGNMENT.json.")

print("Setup completed successfully!")
