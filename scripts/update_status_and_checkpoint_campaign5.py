#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update STATUS.json and CHECKPOINT.json for Campaign 5 (Act 3 Story)."""

import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

def main():
    print("=== UPDATING STATUS.json & CHECKPOINT.json FOR CAMPAIGN 5 ===")
    
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    status["updated_local_date"] = "2026-10-24"
    status["total_narrative_relocalized_lines"] = 18557
    status["total_narrative_relocalized_scenes"] = 277
    
    status["act3_story_campaign"] = {
        "run_id": "act3_story_editorial_20261024_r01",
        "status": "COMPLETED",
        "verdict": "APPROVED_FOR_RELEASE",
        "completion_date": "2026-10-24",
        "total_scenes": 25,
        "total_lines": 3333,
        "partitions": {
            "PARTITION_A": {
                "role": "TRANSLATOR_ACT3_A",
                "scenes": 12,
                "lines": 1585,
                "scope": "Main Story Act 3 Part 1 (STm08_10 to STm08_18_b)",
                "verdict": "APPROVED_100_PERCENT"
            },
            "PARTITION_B": {
                "role": "TRANSLATOR_ACT3_B",
                "scenes": 13,
                "lines": 1748,
                "scope": "Main Story Act 3 Part 2 (STm08_19_a to STm08_21) & Allies Phone Messages (PM11601 to PM12001)",
                "verdict": "APPROVED_100_PERCENT"
            }
        },
        "qa_reviewer": {
            "role": "LOCALIZATION_QA_REVIEWER_ACT3",
            "verdict": "APPROVED_FOR_RELEASE",
            "blockers": 0,
            "majors": 0,
            "minors": 0,
            "pass_rate": "100.00%"
        },
        "deliverable_zip": "dist/StellaSora_Act3_Story_LightNovel_VI_20261024_r01.zip",
        "deliverable_sha256": "cb8a2af33152c27522e949072f3b7c1a7371dbe48e1cd0f6012bc4c580c51711",
        "unified_proposals": "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl"
    }
    
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {STATUS_PATH} (total narrative lines: 18,557)")
    
    checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    checkpoint["updated_local_date"] = "2026-10-24"
    checkpoint["phase"] = "PHASE_CAMPAIGN_5_ACT3_STORY_COMPLETED"
    checkpoint["active_batch"] = "ACT3_STORY_AND_ALLIES_PHONE_3333_LINES"
    checkpoint["batch_status"] = "100_percent_completed_and_approved"
    checkpoint["total_relocalized_lines"] = 18557
    
    CHECKPOINT_PATH.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {CHECKPOINT_PATH}")

if __name__ == "__main__":
    main()
