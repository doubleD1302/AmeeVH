#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staging Campaign 11 (Đợt 3: Character CG Stories Part 2: CG_133 to CG_147) into batch files.
2,726 lines from UNIFIED_CG_PART2_PROPOSALS.jsonl across 30 scenes.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_FILE = ROOT / "work/editorial/character_cg_part2_editorial_20261024_r01/UNIFIED_CG_PART2_PROPOSALS.jsonl"

TARGET_BATCHES = [
    ROOT / "work/batches/batch_10k_b2_partC.json",
    ROOT / "work/batches/batch_10k_b2_partC_translated.json",
    ROOT / "work/batches/batch_10k_b2_approved.json",
]

def main():
    print("Loading proposals from Campaign 11...")
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

    print(f"Loaded {len(campaign_map)} proposals from Campaign 11.")

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
