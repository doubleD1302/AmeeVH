#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 16 (Đợt 8) completion.
Event Stories Part 4 (FINAL EVENT STORIES: STev_09, STev_10, STev_11, STev_12: 3,440 lines across 35 scenes).
Cumulative narrative total: 59,403 lines. 100% OF ALL EVENT STORIES (STev) IN GAME COMPLETED!
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Event_Stories_Part4_LightNovel_VI_20261025_r01.zip"

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
    status["campaign_16_event_stories_part4"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "event_stories_part4_editorial_20261025_r01",
        "total_lines": 3440,
        "total_scenes": 35,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Event_Stories_Part4_LightNovel_VI_20261025_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/EVENT_STORIES_PART4_LIGHTNOVEL_VI_DELIVERY_20261025_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 59403
    status["event_stories_completion"] = "100_PERCENT_COMPLETED"

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-25"
    chk["phase"] = "PHASE_CAMPAIGN_16_ALL_EVENT_STORIES_COMPLETED"
    chk["active_batch"] = "EVENT_STORIES_PART4_3440_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "event_stories_part4_editorial_20261025_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 59403
    chk["event_stories_completion"] = "100_PERCENT_COMPLETED"
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["event_stories_part4"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Event_Stories_Part4_LightNovel_VI_20261025_r01.zip",
        "sha256": zip_sha,
        "lines": 3440,
        "scenes": 35
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
