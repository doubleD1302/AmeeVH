#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partition the 49 missing PM scenes into Partition A and Partition B.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/phone_messages_phase2_20261024_r01"

def main():
    src_file = CAMPAIGN_DIR / "ALL_MISSING_PM_ITEMS.json"
    with open(src_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    all_scenes = sorted(list(set(it["scene_id"] for it in items)))
    mid = len(all_scenes) // 2
    part_a_scenes = set(all_scenes[:mid])
    part_b_scenes = set(all_scenes[mid:])

    part_a = [it for it in items if it["scene_id"] in part_a_scenes]
    part_b = [it for it in items if it["scene_id"] in part_b_scenes]

    diag_a = sum(1 for i in part_a if not i.get("is_tech"))
    diag_b = sum(1 for i in part_b if not i.get("is_tech"))

    print(f"Total scenes: {len(all_scenes)}")
    print(f"Part A: {len(part_a_scenes)} scenes, {len(part_a)} items ({diag_a} dialogues)")
    print(f"Part B: {len(part_b_scenes)} scenes, {len(part_b)} items ({diag_b} dialogues)")

    with open(CAMPAIGN_DIR / "PARTITION_A_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(part_a, f, ensure_ascii=False, indent=2)

    with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "w", encoding="utf-8") as f:
        json.dump(part_b, f, ensure_ascii=False, indent=2)

    print("Partition source files successfully created.")

if __name__ == "__main__":
    main()
