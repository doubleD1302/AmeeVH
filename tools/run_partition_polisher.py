#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polisher runner for a single partition.
Can be invoked by subagents with custom tweaks or verification.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from dialogue_polish_engine import polish_sentence, verify_tokens_preserved

CAMPAIGN_DIR = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01"


def process_partition(part_num: int):
    src_file = CAMPAIGN_DIR / f"PARTITION_{part_num}_SOURCE.jsonl"
    out_file = CAMPAIGN_DIR / f"PARTITION_{part_num}_POLISHED.jsonl"
    report_file = CAMPAIGN_DIR / f"PARTITION_{part_num}_REPORT.json"

    assert src_file.is_file(), f"Source partition file missing: {src_file}"

    lines = [json.loads(l) for l in src_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    total = len(lines)
    print(f"Partition {part_num}: Processing {total} lines...")

    polished_items = []
    modified_count = 0
    token_failures = []

    for item in lines:
        en = item["en"]
        cur_vi = item["current_vi"]
        tokens = item.get("tokens", [])

        polished_vi = polish_sentence(en, cur_vi)

        # Token check
        ok, missing = verify_tokens_preserved(en, polished_vi, tokens)
        if not ok:
            # Fallback preserve original if token lost
            polished_vi = cur_vi
            token_failures.append({"id": item["global_id"], "missing": missing})

        is_modified = (polished_vi != cur_vi)
        if is_modified:
            modified_count += 1

        polished_items.append({
            "global_id": item["global_id"],
            "partition_id": item["partition_id"],
            "en": en,
            "original_vi": cur_vi,
            "polished_vi": polished_vi,
            "modified": is_modified
        })

    with open(out_file, "w", encoding="utf-8") as f:
        for it in polished_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    report = {
        "partition": part_num,
        "total_lines": total,
        "modified_count": modified_count,
        "modified_percent": round(modified_count / total * 100, 2),
        "token_failures": len(token_failures),
        "output_file": str(out_file)
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✓ Partition {part_num} complete: {modified_count}/{total} lines improved ({report['modified_percent']}%). {len(token_failures)} token failures.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--partition", type=int, required=True, choices=[1, 2, 3, 4, 5, 6])
    args = parser.parse_args()
    process_partition(args.partition)
