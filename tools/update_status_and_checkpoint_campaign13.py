#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 13 (Đợt 5) completion.
Special Side Stories Part 2 & Event Story 1 (STsp_12 to STsp_18, STev_01: 3,233 lines across 33 scenes).
Cumulative narrative total: 49,826 lines across 543 scenes.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Side_Stories_Part2_LightNovel_VI_20261025_r01.zip"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    zip_sha = sha256_file(ZIP_PATH) if ZIP_PATH.exists() else ""

    # 1. Update STATUS.json
    with open(STATUS_PATH, "r", encoding="utf-8") as f:
        status = json.load(f)

    status["updated_local_date"] = "2026-10-25"
    status["campaign_13_side_stories_part2"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "side_stories_part2_editorial_20261025_r01",
        "total_lines": 3233,
        "total_scenes": 33,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Side_Stories_Part2_LightNovel_VI_20261025_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/SIDE_STORIES_PART2_LIGHTNOVEL_VI_DELIVERY_20261025_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 49826
    status["total_relocalized_scenes"] = 543

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-25"
    chk["phase"] = "PHASE_CAMPAIGN_13_SIDE_STORIES_PART2_COMPLETED"
    chk["active_batch"] = "SIDE_STORIES_PART2_3233_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "side_stories_part2_editorial_20261025_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 49826
    chk["total_relocalized_scenes"] = 543
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["side_stories_part2"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Side_Stories_Part2_LightNovel_VI_20261025_r01.zip",
        "sha256": zip_sha,
        "lines": 3233,
        "scenes": 33
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
