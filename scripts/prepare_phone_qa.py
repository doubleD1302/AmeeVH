import json
import os

run_id = "phone_messages_editorial_20261024_r01"
run_dir = f"StellaSora_VietHoa/work/runs/{run_id}"
qa_dir = f"StellaSora_VietHoa/work/subagents/{run_id}/qa_reviewer_phone"
os.makedirs(qa_dir, exist_ok=True)

task_packet = {
    "schema": 1,
    "run_id": run_id,
    "task_id": "qa_reviewer_phone",
    "role": "LOCALIZATION_QA_REVIEWER_PHONE",
    "project_root": "C:/YostarGames/StellaSora_EN/StellaSora_VietHoa",
    "objective": "Independently review frozen phone message proposals (3,280 lines across 24 scenes) against instant messaging tone, character voice bible compliance, choice tags preservation, and UTF-8 NFC integrity.",
    "authorization_scope": "Independent localization QA review of Phone Messages under prompt RELOCALIZE_STORY_LIGHTNOVEL_VI_SUBAGENTS_20261023_r02.txt",
    "input_snapshots": [
        {"path": f"work/subagents/{run_id}/translator_phone_a/PROPOSALS.json", "version": "r01"},
        {"path": f"work/subagents/{run_id}/translator_phone_b/PROPOSALS.json", "version": "r01"},
        {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_BIBLE.md", "version": "r02"},
        {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_PROFILES.json", "version": "r02"},
        {"path": "docs/EDITORIAL_QA_RUBRIC.md", "version": "local"}
    ],
    "allowed_write_paths": [f"work/subagents/{run_id}/qa_reviewer_phone/"],
    "output_report": f"work/subagents/{run_id}/qa_reviewer_phone/RESULT.json",
    "task_status": "standby_awaiting_proposals"
}

packet_path = os.path.join(run_dir, "qa_reviewer_phone.task.json")
with open(packet_path, "w", encoding="utf-8") as f:
    json.dump(task_packet, f, ensure_ascii=False, indent=2)

print(f"Created QA task packet: {packet_path}")
