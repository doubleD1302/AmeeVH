#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge Partition A and Partition B for Campaign 5: Act 3 Story & Allies Phone.
Run ID: act3_story_editorial_20261024_r01
Outputs UNIFIED_ACT3_PROPOSALS.jsonl (3,333 lines).
"""

import json
import hashlib
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
RUN_ID = "act3_story_editorial_20261024_r01"
EDITORIAL_DIR = ROOT / "work/editorial" / RUN_ID
SUBAGENT_BASE = ROOT / "work/subagents" / RUN_ID

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    print(f"=== MERGING PARTITIONS FOR {RUN_ID} ===")
    
    p_a_path = SUBAGENT_BASE / "translator_act3_a" / "PROPOSALS.jsonl"
    p_b_path = SUBAGENT_BASE / "translator_act3_b" / "PROPOSALS.jsonl"
    out_path = EDITORIAL_DIR / "UNIFIED_ACT3_PROPOSALS.jsonl"
    
    assert p_a_path.exists(), f"Missing {p_a_path}"
    assert p_b_path.exists(), f"Missing {p_b_path}"
    
    lines_a = [json.loads(l) for l in p_a_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    lines_b = [json.loads(l) for l in p_b_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    
    print(f"Loaded Partition A: {len(lines_a)} lines")
    print(f"Loaded Partition B: {len(lines_b)} lines")
    
    total = lines_a + lines_b
    assert len(total) == 3333, f"Expected 3333 lines, got {len(total)}"
    
    # Check against batch_10k_b3_partC.json
    orig = json.load(open(ROOT / "work/batches/batch_10k_b3_partC.json", encoding="utf-8"))
    orig_keys = set(orig.keys())
    unified_keys = set(it["id"] for it in total)
    diff = orig_keys - unified_keys
    assert not diff, f"Missing keys from original batch: {diff}"
    
    # Write unified file
    EDITORIAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for it in total:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    sha = sha256_file(out_path)
    size = out_path.stat().st_size
    print(f"\nSUCCESS! Created {out_path}:")
    print(f"  Lines: {len(total)}")
    print(f"  Size: {size:,} bytes")
    print(f"  SHA256: {sha}")

if __name__ == "__main__":
    main()
