import json
import os
import hashlib

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

run_dir = "StellaSora_VietHoa/work/runs/lightnovel_editorial_20261024_r02"
subagent_base = "StellaSora_VietHoa/work/subagents/lightnovel_editorial_20261024_r02"

tasks_meta = [
    {
        "task_id": "translator_main_1",
        "role": "TRANSLATOR_MAIN_STORY_1",
        "desc": "Translate Main Story Prologue & Act 1 (Amber, Iris, awakening, Tyrant encounter) into modern Light Novel Vietnamese.",
        "input_partition": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_1/PARTITION_A1_CANDIDATES.json",
        "write_dir": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_1/"
    },
    {
        "task_id": "translator_main_2",
        "role": "TRANSLATOR_MAIN_STORY_2",
        "desc": "Translate Main Story Act 2 (Tilia, Treant & Ancient City Monolith Expedition) into modern Light Novel Vietnamese.",
        "input_partition": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_2/PARTITION_A2_CANDIDATES.json",
        "write_dir": "work/subagents/lightnovel_editorial_20261024_r02/translator_main_2/"
    },
    {
        "task_id": "translator_dating_star",
        "role": "TRANSLATOR_DATING_STAR_TOWER",
        "desc": "Translate Dating Event Interactions, Star Tower Encounters & Character Dossiers into modern Light Novel Vietnamese.",
        "input_partition": "work/subagents/lightnovel_editorial_20261024_r02/translator_dating_star/PARTITION_B1_CANDIDATES.json",
        "write_dir": "work/subagents/lightnovel_editorial_20261024_r02/translator_dating_star/"
    },
    {
        "task_id": "translator_char_stories",
        "role": "TRANSLATOR_CHARACTER_STORIES",
        "desc": "Translate Character Heroine CG Stories (Kasimira, Jinglin, Noya, Minova, Laru, Shia) into modern Light Novel Vietnamese.",
        "input_partition": "work/subagents/lightnovel_editorial_20261024_r02/translator_char_stories/PARTITION_B2_CANDIDATES.json",
        "write_dir": "work/subagents/lightnovel_editorial_20261024_r02/translator_char_stories/"
    }
]

common_inputs = [
    {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_BIBLE.md", "version": "r02"},
    {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_PROFILES.json", "version": "r02"},
    {"path": "work/character_context_20261023_r02/CHARACTER_RELATIONSHIP_MATRIX.json", "version": "r02"}
]

created_task_files = []
for t in tasks_meta:
    task_packet = {
        "schema": 1,
        "run_id": "lightnovel_editorial_20261024_r02",
        "task_id": t["task_id"],
        "role": t["role"],
        "project_root": "C:/YostarGames/StellaSora_EN/StellaSora_VietHoa",
        "objective": t["desc"],
        "input_snapshots": common_inputs + [{"path": t["input_partition"], "version": "r02", "sha256": sha256_file(os.path.join("StellaSora_VietHoa", t["input_partition"].replace("work/", "work/")))}],
        "allowed_write_paths": [t["write_dir"]],
        "shared_paths_reserved_for_root": [
            "STATUS.json",
            "CHECKPOINT.json",
            "config/glossary.json",
            "work/runs/lightnovel_editorial_20261024_r02/RUN.json"
        ],
        "completion_criteria": [
            "100% of candidate dialogues translated into lively modern Light Novel Vietnamese tone",
            "Strict adherence to Voice Bible pronouns and personality markers",
            "Strict preservation of technical tokens: ==PLAYER_NAME==, <color=...>, {0}, \\n",
            "Natural Vietnamese sentence structures; restrained humor; zero calques, street slang, or memes",
            "NFC Unicode UTF-8 compliance",
            "Outputs generated: PROPOSALS.json (or proposals.jsonl), AUDIT.json, and RESULT.json"
        ],
        "output_report": f"{t['write_dir']}RESULT.json",
        "task_status": "assigned"
    }
    packet_path = os.path.join(run_dir, f"{t['task_id']}.task.json")
    with open(packet_path, "w", encoding="utf-8") as f:
        json.dump(task_packet, f, ensure_ascii=False, indent=2)
    created_task_files.append((t["task_id"], packet_path, t["role"], t["write_dir"]))
    print(f"Created task packet: {packet_path}")

# Update RUN.json
run_json_path = os.path.join(run_dir, "RUN.json")
with open(run_json_path, "r", encoding="utf-8") as f:
    run_data = json.load(f)

# Update catalog task to completed
for task in run_data["tasks"]:
    if task["task_id"] == "catalog_preparation":
        task["status"] = "completed"

# Release catalog lease
for lease in run_data["write_leases"]:
    if lease["owner"] == "catalog_preparation":
        lease["state"] = "released"

# Add new tasks and write leases
for tid, ppath, role, wdir in created_task_files:
    if not any(x["task_id"] == tid for x in run_data["tasks"]):
        run_data["tasks"].append({
            "task_id": tid,
            "status": "ready",
            "packet": f"work/runs/lightnovel_editorial_20261024_r02/{tid}.task.json",
            "agent_id": None,
            "role": role,
            "result_path": f"{wdir}RESULT.json"
        })
    if not any(x["owner"] == tid for x in run_data["write_leases"]):
        run_data["write_leases"].append({
            "owner": tid,
            "path": wdir,
            "state": "active"
        })

if "catalog_preparation" not in run_data.get("accepted_task_ids", []):
    run_data.setdefault("accepted_task_ids", []).append("catalog_preparation")

run_data["run_status"] = "translation_in_progress"

with open(run_json_path, "w", encoding="utf-8") as f:
    json.dump(run_data, f, ensure_ascii=False, indent=2)

print("RUN.json successfully updated with 4 parallel translation subagent tasks.")
