#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staging Campaign 10 (Đợt 2: Act 4 Final Climax Story: STm09_00_a to STm09_07_a) into batch files.
2,923 lines from UNIFIED_ACT4_STORY_PROPOSALS.jsonl across 21 scenes.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_FILE = ROOT / "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl"

TARGET_BATCHES = [
    ROOT / "work/batches/batch_10k_b4_partA.json",
    ROOT / "work/batches/batch_10k_b4_partA_translated.json",
    ROOT / "work/batches/batch_10k_b4_partA_qa_approved.json",
    ROOT / "work/batches/batch_10k_b4_approved.json",
]

def main():
    print("Loading proposals from Campaign 10...")
    campaign_map = {}
    with open(CAMPAIGN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            iid = item["id"]
            vi = item.get("vi_editorial")
            if vi and vi.strip():
                campaign_map[iid] = vi.strip()

    print(f"Loaded {len(campaign_map)} proposals from Campaign 10.")

    for batch_path in TARGET_BATCHES:
        batch_data = {}
        if batch_path.exists():
            with open(batch_path, "r", encoding="utf-8") as f:
                batch_data = json.load(f)

        updated = 0
        for k in campaign_map:
            batch_data[k] = campaign_map[k]
            updated += 1

        with open(batch_path, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        print(f"Updated {updated} entries in {batch_path.name} (Total: {len(batch_data)}).")

if __name__ == "__main__":
    main()
