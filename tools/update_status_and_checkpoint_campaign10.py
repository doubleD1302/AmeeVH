#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 10 completion.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Act4_Final_Story_LightNovel_VI_20261024_r01.zip"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    zip_sha = sha256_file(ZIP_PATH) if ZIP_PATH.exists() else ""
    zip_size = ZIP_PATH.stat().st_size if ZIP_PATH.exists() else 0

    # 1. Update STATUS.json
    with open(STATUS_PATH, "r", encoding="utf-8") as f:
        status = json.load(f)

    status["updated_local_date"] = "2026-10-24"
    status["campaign_10_act4_final_story"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "act4_final_story_editorial_20261024_r01",
        "total_lines": 2923,
        "total_scenes": 21,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Act4_Final_Story_LightNovel_VI_20261024_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/ACT4_FINAL_STORY_LIGHTNOVEL_VI_DELIVERY_20261024_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 40931
    status["total_relocalized_scenes"] = 446

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-24"
    chk["phase"] = "PHASE_CAMPAIGN_10_ACT4_FINAL_STORY_COMPLETED"
    chk["active_batch"] = "ACT4_FINAL_STORY_2923_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "act4_final_story_editorial_20261024_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 40931
    chk["total_relocalized_scenes"] = 446
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["act4_final_story"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Act4_Final_Story_LightNovel_VI_20261024_r01.zip",
        "sha256": zip_sha,
        "lines": 2923,
        "scenes": 21
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
