#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staging Campaign 13 (Đợt 5: Special Side Stories Part 2 & Event Story 1) into batch files.
3,233 lines from UNIFIED_CAMPAIGN13_PROPOSALS.jsonl across 33 scenes.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_FILE = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl"

TARGET_BATCHES = [
    ROOT / "work/batches/batch_10k_b4_approved.json",
    ROOT / "work/batches/batch_10k_b4_partB.json",
    ROOT / "work/batches/batch_10k_b4_partB_translated.json",
    ROOT / "work/batches/batch_10k_b4_partB_qa_approved.json",
    ROOT / "work/batches/batch_10k_b4_partC.json",
    ROOT / "work/batches/batch_10k_b4_partC_translated.json",
    ROOT / "work/batches/batch_10k_b4_partC_qa_approved.json",
]

def main():
    print("Loading proposals from Campaign 13...")
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

    print(f"Loaded {len(campaign_map)} proposals from Campaign 13.")

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
