#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 14 (Đợt 6) completion.
Event Stories Part 2 & Dungeon Intros (DP_multi, DP_single, STev_02, STev_03, STev_04: 3,214 lines across 49 scenes).
Cumulative narrative total: 53,040 lines across 590 scenes.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Event_Stories_Part2_LightNovel_VI_20261025_r01.zip"

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
    status["campaign_14_event_stories_part2"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "event_stories_part2_editorial_20261025_r01",
        "total_lines": 3214,
        "total_scenes": 49,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Event_Stories_Part2_LightNovel_VI_20261025_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/EVENT_STORIES_PART2_LIGHTNOVEL_VI_DELIVERY_20261025_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 53040
    status["total_relocalized_scenes"] = 590

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-25"
    chk["phase"] = "PHASE_CAMPAIGN_14_EVENT_STORIES_PART2_COMPLETED"
    chk["active_batch"] = "EVENT_STORIES_PART2_3214_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "event_stories_part2_editorial_20261025_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 53040
    chk["total_relocalized_scenes"] = 590
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["event_stories_part2"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Event_Stories_Part2_LightNovel_VI_20261025_r01.zip",
        "sha256": zip_sha,
        "lines": 3214,
        "scenes": 49
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
