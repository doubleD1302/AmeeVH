#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to inspect scenes in Partition A and B.
"""

import json
from pathlib import Path
import sys

CAMPAIGN_DIR = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part1_editorial_20261025_r01")

def dump_scene(scene_prefix, partition_file):
    with open(partition_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = [x for x in data if x['scene_id'].startswith(scene_prefix)]
    out_file = CAMPAIGN_DIR / f"dump_{scene_prefix}.txt"
    with open(out_file, 'w', encoding='utf-8') as f:
        for it in items:
            f.write(f"[{it['id']}] EN: {it['en']}\nVI_OLD: {it['current_vi']}\n\n")
    print(f"Dumped {len(items)} items for {scene_prefix} to {out_file.name}")

if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "STsp_01"
    part = CAMPAIGN_DIR / ("PARTITION_A_SOURCE.json" if prefix in ["STsp_01", "STsp_02", "STsp_03", "STsp_04", "STsp_05"] else "PARTITION_B_SOURCE.json")
    dump_scene(prefix, part)
