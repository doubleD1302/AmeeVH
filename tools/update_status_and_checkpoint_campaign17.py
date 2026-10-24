#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update STATUS.json and CHECKPOINT.json after Campaign 17 (Đợt 9) completion.
Tutorial Prologue, System Stories & Final Character CGs (STm10001, STm00, ST_sys, BBm, DP, GD, CG_149..CG_162: 3,263 lines across 41 scenes).
Cumulative narrative total: 62,666 lines.
"""

import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

ZIP_PATH = ROOT / "dist/StellaSora_Tutorial_And_Character_CG_LightNovel_VI_20261025_r01.zip"

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
    status["campaign_17_tutorial_and_character_cg"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "tutorial_and_character_cg_editorial_20261025_r01",
        "total_lines": 3263,
        "total_scenes": 41,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Tutorial_And_Character_CG_LightNovel_VI_20261025_r01.zip",
        "zip_sha256": zip_sha,
        "report": "reports/TUTORIAL_AND_CHARACTER_CG_LIGHTNOVEL_VI_DELIVERY_20261025_r01.md"
    }
    status["total_relocalized_narrative_lines"] = 62666

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print("Updated STATUS.json.")

    # 2. Update CHECKPOINT.json
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        chk = json.load(f)

    chk["updated_local_date"] = "2026-10-25"
    chk["phase"] = "PHASE_CAMPAIGN_17_TUTORIAL_AND_CHARACTER_CG_COMPLETED"
    chk["active_batch"] = "TUTORIAL_AND_CHARACTER_CG_3263_LINES"
    chk["batch_status"] = "100_percent_completed_and_approved"
    chk["active_campaign"] = "tutorial_and_character_cg_editorial_20261025_r01"
    chk["total_verified_lines"] = 62666
    chk["next_campaign"] = {
        "campaign_id": "final_cg_npc_and_disc_editorial_20261025_r01",
        "title": "Campaign 18 (Đợt 10 - FINAL CAMPAIGN OF ENTIRE GAME): CG NPC & Disc Stories (33 scenes, 3,078 lines)",
        "scope": "CG_NPC (8 scenes) + CG_disc4004..4066 (25 scenes) = 33 scenes, 3,078 lines"
    }

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(chk, f, ensure_ascii=False, indent=2)
    print("Updated CHECKPOINT.json.")

if __name__ == "__main__":
    main()
