#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage Campaign 5 (3,333 lines) into working batches:
- work/batches/batch_10k_b3_partC_translated.json
- work/batches/batch_10k_b3_approved.json
"""

import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
RUN_ID = "act3_story_editorial_20261024_r01"
PROPOSALS_PATH = ROOT / "work/editorial" / RUN_ID / "UNIFIED_ACT3_PROPOSALS.jsonl"
BATCH_DIR = ROOT / "work/batches"

def main():
    print(f"=== STAGING {RUN_ID} TO BATCHES ===")
    assert PROPOSALS_PATH.exists(), f"Missing {PROPOSALS_PATH}"
    
    prop_lines = [json.loads(l) for l in PROPOSALS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Loaded {len(prop_lines)} lines from {PROPOSALS_PATH.name}")
    assert len(prop_lines) == 3333, f"Expected 3333 lines, got {len(prop_lines)}"
    
    # 1. Update batch_10k_b3_partC_translated.json
    tr_path = BATCH_DIR / "batch_10k_b3_partC_translated.json"
    tr_data = json.load(open(tr_path, encoding="utf-8")) if tr_path.exists() else {}
    for it in prop_lines:
        lid = it["id"]
        vi = it.get("vi_editorial")
        if vi is not None:
            tr_data[lid] = vi
            
    tr_path.write_text(json.dumps(tr_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {tr_path.name} ({len(tr_data)} items)")
    
    # 2. Update batch_10k_b3_approved.json
    appr_path = BATCH_DIR / "batch_10k_b3_approved.json"
    appr_data = json.load(open(appr_path, encoding="utf-8")) if appr_path.exists() else {}
    updated_in_master = 0
    for it in prop_lines:
        lid = it["id"]
        vi = it.get("vi_editorial")
        if vi is not None and lid in appr_data:
            appr_data[lid] = vi
            updated_in_master += 1
            
    appr_path.write_text(json.dumps(appr_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {appr_path.name} ({updated_in_master} keys updated into 10k master batch)")
    print("\nSTAGING COMPLETE!")

if __name__ == "__main__":
    main()
