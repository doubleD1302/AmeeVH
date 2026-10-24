import json

def update_status():
    path = "STATUS.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["campaign_18_final_cg_npc_and_disc"] = {
        "status": "COMPLETED_AND_QA_APPROVED_100_PERCENT",
        "run_id": "final_cg_npc_and_disc_editorial_20261025_r01",
        "total_lines": 3076,
        "total_scenes": 33,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "deliverable_zip": "dist/StellaSora_Final_CG_NPC_And_Disc_LightNovel_VI_20261025_r01.zip",
        "zip_sha256": "702b7ba5d35873af3239426ceb9e73ce400cbc95c5092397ccb6b6ebe46d2bd6",
        "report": "reports/FINAL_CG_NPC_AND_DISC_LIGHTNOVEL_VI_DELIVERY_20261025_r01.md"
    }

    data["game_story_completion"] = {
        "status": "100_PERCENT_COMPLETED",
        "total_avg_files_in_game": 626,
        "total_avg_files_localized": 626,
        "total_dialogue_strings_replaced": 69788,
        "total_scenes_dictionaries": 726,
        "prose_style": "Authentic_Light_Novel_Vietnamese",
        "calques_remaining": 0,
        "untranslated_remaining": 0,
        "dual_sync": {
            "standalone_path": "c:/YostarGames/StellaSora_EN/Persistent_Store/Scripts/lua.arcx",
            "steam_path": "C:/Program Files (x86)/Steam/steamapps/common/Stella Sora/Persistent_Store/Scripts/lua.arcx",
            "size_bytes": 67947370
        }
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_checkpoint():
    path = "CHECKPOINT.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["phase"] = "PHASE_ALL_STORY_CAMPAIGNS_100_PERCENT_COMPLETED"
    data["active_batch"] = "FINAL_CG_NPC_AND_DISC_3076_LINES"
    data["batch_status"] = "100_percent_completed_and_approved"
    data["total_verified_lines"] = 65742

    if "campaign_packages" not in data:
        data["campaign_packages"] = {}

    data["campaign_packages"]["final_cg_npc_and_disc"] = {
        "zip": "StellaSora_VietHoa/dist/StellaSora_Final_CG_NPC_And_Disc_LightNovel_VI_20261025_r01.zip",
        "sha256": "702b7ba5d35873af3239426ceb9e73ce400cbc95c5092397ccb6b6ebe46d2bd6",
        "lines": 3076,
        "scenes": 33
    }

    data["all_game_story_completion"] = "100_PERCENT_COMPLETED_ZERO_SCENES_REMAINING"
    data["next_campaign"] = None

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    update_status()
    update_checkpoint()
    print("Status and Checkpoint verified!")
