#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 7 completion.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"
ZIP_PATH = ROOT / "dist/StellaSora_Phone_Messages_Phase2_VI_20261024_r01.zip"

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

    status["updated_local_date"] = "2026-10-24"
    status["campaign_7_phone_messages_phase2"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "phone_messages_phase2_20261024_r01",
        "total_items": 8312,
        "dialogue_lines": 7204,
        "total_scenes": 49,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Phone_Messages_Phase2_VI_20261024_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/PHONE_MESSAGES_PHASE2_LIGHTNOVEL_VI_DELIVERY_20261024_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 29095
    status["total_relocalized_scenes"] = 349
    status["phone_messages_all_73_scenes_status"] = "100_PERCENT_COMPLETED_AND_INSTALLED"

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-24"
    chk["phase"] = "PHASE_CAMPAIGN_7_PHONE_MESSAGES_PHASE2_COMPLETED"
    chk["active_batch"] = "PHONE_MESSAGES_PHASE2_49_SCENES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "phone_messages_phase2_20261024_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 29095
    chk["total_relocalized_scenes"] = 349
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["phone_messages_phase2"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Phone_Messages_Phase2_VI_20261024_r01.zip",
        "sha256": zip_sha,
        "items": 8312,
        "dialogues": 7204,
        "scenes": 49
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
