import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
status_path = ROOT / "STATUS.json"
checkpoint_path = ROOT / "CHECKPOINT.json"

status = json.loads(status_path.read_text(encoding="utf-8"))
checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))

integration_record = {
    "status": "COMPLETED_AND_VERIFIED",
    "timestamp": "2026-10-26T08:00:00+07:00",
    "batches_integrated": ["BATCH_01", "BATCH_02", "BATCH_03", "BATCH_04", "BATCH_06"],
    "total_remediated_items": 644,
    "breakdown": {
        "batch_01_mechanics_and_tokens": 56,
        "batch_02_video_subtitles": 44,
        "batch_03_data_untranslated": 196,
        "batch_04_story_short_lines_and_lore": 306,
        "batch_06_polish_data": 39,
        "batch_06_polish_story": 3
    },
    "asset_bundles_reconciled": 27,
    "golden_distribution_artifacts": {
        "data_arcx": {
            "path": "dist/data_patched_vi.arcx",
            "size": 25824664,
            "sha256": "cad216cd685cbb8fd0ef631e57f10536a43462499652fcfdd36ecce66f2f0094"
        },
        "lua_arcx": {
            "path": "dist/lua_patched_vi.arcx",
            "size": 67948864,
            "sha256": "32abce19bcfa51644f120f8dcff8bebe77e763a95c643e797376ec89af6bc890"
        },
        "subtitles_dir": "dist/Videos",
        "asset_bundles_dir": "dist/AssetBundles"
    },
    "dual_deployment": {
        "yostar_client": {
            "path": "c:\\YostarGames\\StellaSora_EN",
            "data_arcx_verified": True,
            "lua_arcx_verified": True,
            "subtitles_verified": True,
            "asset_bundles_verified": True
        },
        "steam_client": {
            "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stella Sora",
            "data_arcx_verified": True,
            "lua_arcx_verified": True,
            "subtitles_verified": True,
            "asset_bundles_verified": True
        }
    },
    "anti_regression_gate": {
        "verified_by": "tools/verify_deployed_game_data.py",
        "discs_check": "PASSED_100_PERCENT",
        "skills_check": "PASSED_100_PERCENT",
        "uitext_check": "PASSED_100_PERCENT",
        "gacha_storage_check": "PASSED_100_PERCENT",
        "hash_parity_check": "MATCH_100_PERCENT"
    }
}

# Update STATUS.json
status["audit_and_remediation_20261026"]["deployment_status"] = "deployed_and_verified_dual_client_yostar_and_steam"
status["audit_and_remediation_20261026"]["integration_record"] = integration_record
status["updated_local_date"] = "2026-10-26"
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated STATUS.json")

# Update CHECKPOINT.json
checkpoint["phase"] = "PHASE_BATCHES_01_TO_06_INTEGRATION_AND_DEPLOYMENT_COMPLETED"
checkpoint["active_batch"] = "BATCHES_01_TO_06_INTEGRATED"
checkpoint["batch_status"] = "deployed_and_verified_in_live_game"
checkpoint["integration_record"] = integration_record
checkpoint["updated_local_date"] = "2026-10-26"
checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated CHECKPOINT.json")
