#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staging Campaign 14 (Đợt 6: Event Stories Part 2 & Dungeon Intros) into batch files.
3,214 lines from UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl across 49 scenes.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_FILE = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl"

TARGET_BATCHES = [
    ROOT / "work/batches/batch_10k_b4_approved.json",
    ROOT / "work/batches/batch_10k_b4_partC.json",
    ROOT / "work/batches/batch_10k_b4_partC_translated.json",
    ROOT / "work/batches/batch_10k_b4_partC_qa_approved.json",
]

def main():
    print("Loading proposals from Campaign 14...")
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

    print(f"Loaded {len(campaign_map)} proposals from Campaign 14.")

    for batch_path in TARGET_BATCHES:
        if not batch_path.exists():
            continue
        with open(batch_path, "r", encoding="utf-8") as f:
            batch_data = json.load(f)

        updated = 0
        for k in campaign_map:
            if k in batch_data:
                batch_data[k] = campaign_map[k]
                updated += 1

        with open(batch_path, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        print(f"Updated {updated} entries in {batch_path.name} (Total: {len(batch_data)}).")

if __name__ == "__main__":
    main()
