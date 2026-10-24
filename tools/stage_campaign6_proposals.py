#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staging Campaign 6 (Act 2 Climax Story / Act 3 Prelude) into batch files.
3,334 lines from UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_FILE = ROOT / "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl"
PART_A_TRANS = ROOT / "work/batches/batch_10k_b3_partA_translated.json"
B3_APPROVED = ROOT / "work/batches/batch_10k_b3_approved.json"

def main():
    print("Loading proposals from Campaign 6...")
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

    print(f"Loaded {len(campaign_map)} proposals.")

    # 1. Update batch_10k_b3_partA_translated.json
    print(f"Updating {PART_A_TRANS.name}...")
    part_a_data = {}
    if PART_A_TRANS.exists():
        with open(PART_A_TRANS, "r", encoding="utf-8") as f:
            part_a_data = json.load(f)
    
    updated_a = 0
    for k, v in campaign_map.items():
        part_a_data[k] = v
        updated_a += 1

    with open(PART_A_TRANS, "w", encoding="utf-8") as f:
        json.dump(part_a_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {updated_a} entries in {PART_A_TRANS.name} (Total: {len(part_a_data)}).")

    # 2. Update batch_10k_b3_approved.json
    print(f"Updating {B3_APPROVED.name}...")
    b3_data = {}
    if B3_APPROVED.exists():
        with open(B3_APPROVED, "r", encoding="utf-8") as f:
            b3_data = json.load(f)

    updated_b3 = 0
    for k, v in campaign_map.items():
        b3_data[k] = v
        updated_b3 += 1

    with open(B3_APPROVED, "w", encoding="utf-8") as f:
        json.dump(b3_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {updated_b3} entries in {B3_APPROVED.name} (Total: {len(b3_data)}).")

if __name__ == "__main__":
    main()
