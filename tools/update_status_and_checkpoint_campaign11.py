#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 11 (Đợt 3) completion.
Character CG Stories Part 2 (CG_133 to CG_147, 2,726 lines across 30 scenes).
Cumulative narrative total: 43,657 lines across 476 scenes.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Character_CG_Part2_LightNovel_VI_20261024_r01.zip"

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
    status["campaign_11_character_cg_part2"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "character_cg_part2_editorial_20261024_r01",
        "total_lines": 2726,
        "total_scenes": 30,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Character_CG_Part2_LightNovel_VI_20261024_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/CHARACTER_CG_PART2_LIGHTNOVEL_VI_DELIVERY_20261024_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 43657
    status["total_relocalized_scenes"] = 476

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-24"
    chk["phase"] = "PHASE_CAMPAIGN_11_CHARACTER_CG_PART2_COMPLETED"
    chk["active_batch"] = "CHARACTER_CG_PART2_2726_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "character_cg_part2_editorial_20261024_r01"
    chk["campaign_status"] = "COMPLETED"
    chk["total_relocalized_lines"] = 43657
    chk["total_relocalized_scenes"] = 476
    chk["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if "latest_deliverables" not in chk:
        chk["latest_deliverables"] = {}
    chk["latest_deliverables"]["character_cg_part2"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Character_CG_Part2_LightNovel_VI_20261024_r01.zip",
        "sha256": zip_sha,
        "lines": 2726,
        "scenes": 30
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
