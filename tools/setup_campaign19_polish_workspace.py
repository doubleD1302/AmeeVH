#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Workspace for Campaign 19: Full Style Polish & Humanization for 20,680 Fallback Dialogue Lines.
Splits 20,680 lines into 6 balanced partitions for 6 parallel subagents:
- Partition 1: Lines 0..3446 (3,447 lines)
- Partition 2: Lines 3447..6893 (3,447 lines)
- Partition 3: Lines 6894..10340 (3,447 lines)
- Partition 4: Lines 10341..13787 (3,447 lines)
- Partition 5: Lines 13788..17233 (3,446 lines)
- Partition 6: Lines 17234..20679 (3,446 lines)
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')


def main():
    print("Setting up Campaign 19 Workspace...")
    src_file = ROOT / "work/batches/remaining_lua_avg_cache.json"
    assert src_file.is_file(), f"Source file missing: {src_file}"

    data = json.load(open(src_file, "r", encoding="utf-8"))
    items = list(data.items())
    total = len(items)
    print(f"Loaded {total} dialogue lines from {src_file.name}")

    # Partition sizes
    num_partitions = 6
    chunk_size = total // num_partitions
    remainder = total % num_partitions

    partitions = []
    start = 0
    for i in range(num_partitions):
        # distribute remainder across first few partitions
        size = chunk_size + (1 if i < remainder else 0)
        end = start + size
        part_items = items[start:end]
        partitions.append((i + 1, start, end, part_items))
        start = end

    print(f"Partition distribution across {num_partitions} subagents:")
    manifest = {
        "campaign": "Campaign 19: Full 20,680 Dialogue Style Polish",
        "created_at": "2026-10-25",
        "total_lines": total,
        "partitions": []
    }

    for p_num, p_start, p_end, p_items in partitions:
        p_filename = f"PARTITION_{p_num}_SOURCE.jsonl"
        p_path = CAMPAIGN_DIR / p_filename
        with open(p_path, "w", encoding="utf-8") as f:
            for idx, (en, cur_vi) in enumerate(p_items):
                global_idx = p_start + idx
                tokens = TAG_PATTERN.findall(en)
                record = {
                    "global_id": global_idx,
                    "partition_id": idx,
                    "en": en,
                    "current_vi": cur_vi,
                    "tokens": tokens,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"  Partition {p_num}: {len(p_items)} lines (indices {p_start}..{p_end-1}) -> {p_filename}")
        manifest["partitions"].append({
            "partition": p_num,
            "filename": p_filename,
            "lines_count": len(p_items),
            "start_index": p_start,
            "end_index": p_end - 1
        })

    with open(CAMPAIGN_DIR / "CAMPAIGN_19_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("✓ Workspace setup completed successfully.")


if __name__ == "__main__":
    main()
