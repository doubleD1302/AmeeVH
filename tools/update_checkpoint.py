#!/usr/bin/env python3
"""Update CHECKPOINT.json with all completed tables from pillars 1-4."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    ckpt_path = ROOT / "CHECKPOINT.json"
    with open(ckpt_path, "r", encoding="utf-8") as f:
        ckpt = json.load(f)

    existing_ids = set(ckpt.get("completed_translation_ids", []))

    # Read approved files
    approved_files = [
        ROOT / "work" / "batches" / "pillar1_approved.json",
        ROOT / "work" / "batches" / "pillar2_approved.json",
        ROOT / "work" / "batches" / "pillar3_approved.json",
        ROOT / "work" / "batches" / "pillar4_approved.json",
    ]

    for ap in approved_files:
        if not ap.exists():
            continue
        with open(ap, "r", encoding="utf-8") as f:
            data = json.load(f)
        for tbl_name, tbl_info in data.items():
            fname = tbl_info.get("file", "")
            cnt = tbl_info.get("count", len(tbl_info.get("entries", {})))
            cid = f"{fname}::{tbl_name}::1..{cnt}"
            existing_ids.add(cid)

    ckpt["updated_local_date"] = "2026-10-20"
    ckpt["phase"] = "major_pillars_translation_and_qa_complete"
    ckpt["batch_status"] = "pillars_1_to_4_qa_approved_and_deployed"
    ckpt["completed_translation_ids"] = sorted(list(existing_ids))
    ckpt["next_action"] = "Ready for full gameplay testing and subsequent AVG dialogue / Lua script expansions."

    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)

    print(f"Updated CHECKPOINT.json with {len(existing_ids)} completed IDs.")

if __name__ == "__main__":
    main()
