#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 13 (Đợt 5):
Special Side Stories Part 2 (STsp_12 to STsp_18: 2,185 lines) + Event Story 1 (STev_01: 1,048 lines)
Total: 33 scenes, 3,233 lines.
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

b4_en_path = ROOT / "work/batches/batch_10000_avg_clean_b4.json"
b4_vi_path = ROOT / "work/batches/batch_10k_b4_approved.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

def main():
    print("Setting up Campaign 13 workspace...")
    en_data = json.load(open(b4_en_path, encoding="utf-8"))
    vi_data = json.load(open(b4_vi_path, encoding="utf-8"))

    part_a_prefixes = ['STsp_12', 'STsp_13', 'STsp_14', 'STsp_15']
    part_b_prefixes = ['STsp_16', 'STsp_17', 'STsp_18', 'STev_01']

    items_a = []
    items_b = []

    for k, en_text in en_data.items():
        sc = k.split(".")[0]
        prefix = sc[:7]

        is_a = any(sc.startswith(p) for p in part_a_prefixes)
        is_b = any(sc.startswith(p) for p in part_b_prefixes)

        if not (is_a or is_b):
            continue

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

        if is_a:
            items_a.append(entry)
        else:
            items_b.append(entry)

    print(f"Partition A: {len(items_a)} items across {len(set(x['scene_id'] for x in items_a))} scenes.")
    print(f"Partition B: {len(items_b)} items across {len(set(x['scene_id'] for x in items_b))} scenes.")
    print(f"Total Campaign 13: {len(items_a) + len(items_b)} items.")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(items_b, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "CAMPAIGN_13_SOURCE_ALL.json", "w", encoding="utf-8") as f:
        json.dump(items_a + items_b, f, ensure_ascii=False, indent=2)

    print("Campaign 13 workspace setup complete!")

if __name__ == "__main__":
    main()
