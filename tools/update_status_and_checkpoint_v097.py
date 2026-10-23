#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update STATUS.json and CHECKPOINT.json for Release v0.9.7."""

import json
from pathlib import Path
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
STATUS_PATH = ROOT / "STATUS.json"
CHECKPOINT_PATH = ROOT / "CHECKPOINT.json"

def main():
    print("=== UPDATING STATUS.json & CHECKPOINT.json FOR v0.9.7 ===")
    
    # Update STATUS.json
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    status["updated_local_date"] = "2026-10-24"
    status["latest_release"] = "v0.9.7"
    status["launcher_pc"] = "launcher/launcher_pc.py (v0.9.7: Manifest-verified sync, SHA256 integrity check, path traversal guard, allowlist check, atomic replace on same volume, rollback journal, and accurate scope reporting)"
    
    status["executable_build"] = {
        "version": "0.9.7",
        "exe_path": "dist/StellaSora_Launcher.exe",
        "size_bytes": 9934599,
        "locations": [
            "C:/YostarGames/StellaSora_EN/StellaSora_Launcher.exe",
            "c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/dist/StellaSora_Launcher.exe",
            "c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/launcher/StellaSora_Launcher.exe"
        ]
    }
    
    status["release_v097"] = {
        "tag": "v0.9.7",
        "title": "Stella Sora Việt Hóa v0.9.7 - Đại Bản Doanh Light Novel (15.224 Dòng Thoại) & 63 AssetBundles Đồ Họa",
        "published_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_narrative_relocalized_lines": 15224,
        "total_narrative_relocalized_scenes": 252,
        "total_asset_bundles": 63,
        "total_textures_patched": 842,
        "deliverables": {
            "offline_bundle": "dist/StellaSora_Launcher_PC.zip (271.80 MB)",
            "asset_bundles": "dist/StellaSora_AssetBundles_VI.zip (85.22 MB)",
            "data_tables_arcx": "dist/data_patched_vi.arcx (25.78 MB)",
            "scripts_avg_arcx": "dist/lua_patched_vi.arcx (67.46 MB)",
            "launcher_executable": "dist/StellaSora_Launcher.exe (9.93 MB)",
            "patch_manifest": "dist/patch_manifest.json"
        },
        "campaigns_breakdown": {
            "campaign_1_story": "5,558 lines (174 scenes)",
            "campaign_2_phone": "3,280 lines (24 scenes)",
            "campaign_3_archives": "1,662 lines (4 tables, purged MT relics)",
            "campaign_4_cg_stories": "4,724 lines (54 scenes, 18 heroines)"
        }
    }
    
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {STATUS_PATH}")
    
    # Update CHECKPOINT.json
    checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    checkpoint["updated_local_date"] = "2026-10-24"
    checkpoint["phase"] = "PHASE_CLIENT_RELEASE_V097_PUBLISHED"
    checkpoint["active_batch"] = "RELEASE_V097_15224_LIGHTNOVEL_AND_63_BUNDLES"
    checkpoint["batch_status"] = "100_percent_completed_and_published_to_github"
    checkpoint["latest_release_tag"] = "v0.9.7"
    
    CHECKPOINT_PATH.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {CHECKPOINT_PATH}")

if __name__ == "__main__":
    main()
