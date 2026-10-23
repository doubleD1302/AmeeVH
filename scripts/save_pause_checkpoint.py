import json
import os
import datetime

run_file = "StellaSora_VietHoa/work/runs/lightnovel_editorial_20261024_r02/RUN.json"
with open(run_file, "r", encoding="utf-8") as f:
    run_data = json.load(f)

# Update tasks
for t in run_data["tasks"]:
    if t["task_id"] == "translator_char_stories":
        t["status"] = "completed"

# Add frozen snapshot for char stories
if not any(s.get("snapshot_id") == "proposals_char_stories" for s in run_data.get("frozen_snapshots", [])):
    run_data.setdefault("frozen_snapshots", []).append({
        "snapshot_id": "proposals_char_stories",
        "path": "work/subagents/lightnovel_editorial_20261024_r02/translator_char_stories/PROPOSALS.json",
        "sha256": "4242fbb141ba3debaad37db50d7b30d3ca12cdcc5537a01d5a3b92e14491242a",
        "lines": 1289
    })

run_data["pause_checkpoint"] = {
    "timestamp": datetime.datetime.now().isoformat(),
    "reason": "User requested pause to switch accounts",
    "ready_to_resume": True,
    "resumption_prompt": "Tiếp tục chiến dịch Light Novel Story Editorial từ RUN lightnovel_editorial_20261024_r02: nhận nốt kết quả từ TRANSLATOR_DATING_STAR_TOWER và QA Reviewer, sau đó tổng hợp UNIFIED_STORY_PROPOSALS."
}

with open(run_file, "w", encoding="utf-8") as f:
    json.dump(run_data, f, ensure_ascii=False, indent=2)

# Write CHECKPOINT_PAUSE.json
checkpoint_pause_path = "StellaSora_VietHoa/work/runs/lightnovel_editorial_20261024_r02/CHECKPOINT_PAUSE.json"
with open(checkpoint_pause_path, "w", encoding="utf-8") as f:
    json.dump({
        "schema": 1,
        "run_id": "lightnovel_editorial_20261024_r02",
        "paused_at": datetime.datetime.now().isoformat(),
        "total_lines_target": 5558,
        "completed_lines": 4550,
        "completed_tasks": [
            "catalog_preparation",
            "translator_main_1",
            "translator_main_2",
            "translator_char_stories"
        ],
        "active_background_tasks": [
            "translator_dating_star",
            "localization_qa_review"
        ],
        "frozen_proposals": run_data["frozen_snapshots"],
        "resume_instructions": "Khi quay lại, chỉ cần nói 'tiếp tục', agent sẽ đọc CHECKPOINT_PAUSE.json và RUN.json để hoàn thiện khâu QA, tổng hợp UNIFIED_STORY_PROPOSALS và bàn giao."
    }, f, ensure_ascii=False, indent=2)

print("Checkpoint files created successfully.")
