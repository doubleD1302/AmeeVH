#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace and Partitions for Campaign 11 (Đợt 3):
Character CG Stories Part 2 (CG_133 to CG_147, 10 Trekkers, 30 scenes, 2,726 dialogue lines).
- Part A: CG_133, CG_135, CG_137, CG_139, CG_140 (15 scenes, 1,351 lines)
  Trekkers: Nazuka, Mistique, Eleanor, Allie, Sparkla
- Part B: CG_141, CG_142, CG_143, CG_145, CG_147 (15 scenes, 1,375 lines)
  Trekkers: Chixia, Cosette, Wraith, Otoha, Caramel
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
WORK_DIR = ROOT / "work" / "editorial" / "character_cg_part2_editorial_20261024_r01"
WORK_DIR.mkdir(parents=True, exist_ok=True)

b2_en_path = ROOT / "work/batches/batch_10000_avg_clean_b2.json"
b2_vi_path = ROOT / "work/batches/batch_10k_b2_approved.json"

en_data = json.load(open(b2_en_path, encoding="utf-8"))
vi_data = json.load(open(b2_vi_path, encoding="utf-8"))

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

part_a_scenes = [
    'CG_133_01', 'CG_133_02', 'CG_133_03', 
    'CG_135_01', 'CG_135_02', 'CG_135_03', 
    'CG_137_01', 'CG_137_02', 'CG_137_03', 
    'CG_139_01', 'CG_139_02', 'CG_139_03', 
    'CG_140_01', 'CG_140_02', 'CG_140_03'
]

part_b_scenes = [
    'CG_141_01', 'CG_141_02', 'CG_141_03', 
    'CG_142_01', 'CG_142_02', 'CG_142_03', 
    'CG_143_01', 'CG_143_02', 'CG_143_03', 
    'CG_145_01', 'CG_145_02', 'CG_145_03', 
    'CG_147_01', 'CG_147_02', 'CG_147_03'
]

items_a = []
items_b = []

for k, en_text in en_data.items():
    sc = k.split(".")[0]
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
    
    if sc in part_a_scenes:
        items_a.append(entry)
    elif sc in part_b_scenes:
        items_b.append(entry)

# Write JSONL
with open(WORK_DIR / "PARTITION_CG_PART2_A.jsonl", "w", encoding="utf-8") as f:
    for item in items_a:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

with open(WORK_DIR / "PARTITION_CG_PART2_B.jsonl", "w", encoding="utf-8") as f:
    for item in items_b:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# Write JSON arrays for source reference
with open(WORK_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_a, f, ensure_ascii=False, indent=2)

with open(WORK_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
    json.dump(items_b, f, ensure_ascii=False, indent=2)

print(f"Setup Complete:")
print(f"  Partition A: {len(items_a)} lines across {len(part_a_scenes)} scenes")
print(f"  Partition B: {len(items_b)} lines across {len(part_b_scenes)} scenes")
print(f"  Total Campaign 11 Lines: {len(items_a) + len(items_b)}")
