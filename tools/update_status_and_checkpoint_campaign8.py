#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 8 completion.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Act1_Act2_Story_LightNovel_VI_20261024_r01.zip"

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
    status["campaign_8_act1_climax_act2_story"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "act1_act2_story_editorial_20261024_r01",
        "total_lines": 5580,
        "total_scenes": 46,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Act1_Act2_Story_LightNovel_VI_20261024_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/ACT1_ACT2_STORY_LIGHTNOVEL_VI_DELIVERY_20261024_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 34675
    status["total_relocalized_scenes"] = 395

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-24"
    chk["phase"] = "PHASE_CAMPAIGN_8_ACT1_ACT2_STORY_COMPLETED"
    chk["active_batch"] = "ACT1_ACT2_STORY_5580_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "act1_act2_story_editorial_20261024_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 34675
    chk["total_relocalized_scenes"] = 395
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["act1_act2_story"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Act1_Act2_Story_LightNovel_VI_20261024_r01.zip",
        "sha256": zip_sha,
        "lines": 5580,
        "scenes": 46
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
