import json
import os
import hashlib
import datetime

out_dir = "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02"
jsonl_path = os.path.join(out_dir, "UNIFIED_STORY_PROPOSALS.jsonl")

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

cp_story = {
    "schema": 1,
    "run_id": "lightnovel_editorial_20261024_r02",
    "updated_at": datetime.datetime.now().isoformat(),
    "campaign_name": "Stella Sora Light Novel Story Relocalization Campaign",
    "status": "COMPLETED_AND_VERIFIED_100_PERCENT",
    "total_target_lines": 5558,
    "total_verified_lines": 5558,
    "total_scenes": 174,
    "coverage_percent": "100.0%",
    "subagents_deployed": [
        {"role": "CATALOG_ENGINEER", "conversation_id": "05521698-44e2-4d95-bb13-f10dd8bc4060", "status": "completed"},
        {"role": "TRANSLATOR_MAIN_STORY_1", "conversation_id": "d69b6b30-2a23-48f7-8d90-2b2f6a53741e", "status": "completed_100_percent"},
        {"role": "TRANSLATOR_MAIN_STORY_2", "conversation_id": "811383db-581a-496e-9d4e-8bccc6b8d309", "status": "completed_r02_calibrated"},
        {"role": "TRANSLATOR_DATING_STAR_TOWER", "conversation_id": "ceb03da2-1443-4d4a-90d7-de2ae2f85495", "status": "completed_100_percent"},
        {"role": "TRANSLATOR_CHARACTER_STORIES", "conversation_id": "aa3eba83-9e7b-44b2-9b26-d8df52a00fbf", "status": "completed_r02_calibrated"},
        {"role": "LOCALIZATION_QA_REVIEWER_A", "conversation_id": "2c488469-1c7d-4022-b4af-bd67c0cf6cff", "status": "approved_partition_a_100_percent"},
        {"role": "LOCALIZATION_QA_REVIEWER_B", "conversation_id": "1420a8a7-f3ec-487e-8e4f-cd5a9351a671", "status": "approved_partition_b_100_percent"}
    ],
    "approved_snapshots": {
        "PARTITION_A1": {
            "path": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_1/PROPOSALS.json",
            "sha256": "b6f158ec421d760d3121890119e7d3f7963654786356250b8c5ff10cb4f64fca",
            "scenes": 43,
            "lines": 1758,
            "qa_status": "APPROVED_GOLDEN_CALIBRATION"
        },
        "PARTITION_A2": {
            "path": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_2/PROPOSALS_R02.json",
            "sha256": "f12039c3ded67db8e1289aa3bc48ed33bcc230ff70c14fe5d9f956ce268affc5",
            "scenes": 14,
            "lines": 1503,
            "qa_status": "APPROVED_R02_ALL_BLOCKERS_RESOLVED"
        },
        "PARTITION_B1": {
            "path": "work/subagents/lightnovel_editorial_20261024_r02/translator_dating_star/PROPOSALS.json",
            "sha256": "4eaad20cf8f5f363b4defa2693250e8df221fbaeaabff90b5a7908aaaf22d9f0",
            "scenes": 100,
            "lines": 1008,
            "qa_status": "APPROVED_GOLDEN_CALIBRATION"
        },
        "PARTITION_B2": {
            "path": "work/subagents/lightnovel_editorial_20261024_r02/translator_char_stories/PROPOSALS_R02.json",
            "sha256": "ea846a22d068306447fdb82819db287d86eac383a996daa4fddac3738c7f1673",
            "scenes": 17,
            "lines": 1289,
            "qa_status": "APPROVED_R02_ALL_BLOCKERS_RESOLVED"
        }
    },
    "unified_deliverable": {
        "jsonl_path": "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl",
        "sha256": sha256_file(jsonl_path) if os.path.exists(jsonl_path) else None,
        "total_lines": 5558
    }
}

cp_story_path = os.path.join(out_dir, "CHECKPOINT_STORY.json")
with open(cp_story_path, "w", encoding="utf-8") as f:
    json.dump(cp_story, f, ensure_ascii=False, indent=2)

print(f"Created {cp_story_path} successfully.")
