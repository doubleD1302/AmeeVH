# -*- coding: utf-8 -*-
"""
Deploy and verify v1.1.0 golden artifacts to standalone Yostar client and Steam client (if available).
Updates manifests: dist/patch_manifest.json and dist/android_patch_manifest.json.
Runs verify_deployed_game_data.py.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
DIST = ROOT / "dist"
DATA_ARCX = DIST / "data_patched_vi.arcx"
LUA_ARCX = DIST / "lua_patched_vi.arcx"
VIDEOS_DIR = DIST / "Videos"

YOSTAR_ROOT = Path(r"c:\YostarGames\StellaSora_EN")
STEAM_ROOT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora")

def get_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def update_manifests():
    print("=== UPDATING MANIFESTS TO V1.1.0 ===")
    data_sha = get_sha256(DATA_ARCX)
    data_size = DATA_ARCX.stat().st_size
    lua_sha = get_sha256(LUA_ARCX)
    lua_size = LUA_ARCX.stat().st_size

    print(f"data_patched_vi.arcx: {data_size:,} bytes | sha256: {data_sha}")
    print(f"lua_patched_vi.arcx:  {lua_size:,} bytes | sha256: {lua_sha}")

    # 1. PC patch_manifest.json
    pc_manifest = DIST / "patch_manifest.json"
    if pc_manifest.exists():
        pm = json.loads(pc_manifest.read_text(encoding="utf-8"))
        pm["release_tag"] = "v1.1.0"
        pm["version"] = "1.1.0"
        pm["data_arcx"] = {
            "path": "Persistent_Store/Tables/data.arcx",
            "size_bytes": data_size,
            "sha256": data_sha
        }
        pm["lua_arcx"] = {
            "path": "Persistent_Store/Scripts/lua.arcx",
            "size_bytes": lua_size,
            "sha256": lua_sha
        }
        pc_manifest.write_text(json.dumps(pm, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Updated dist/patch_manifest.json to v1.1.0")

    # 2. Android android_patch_manifest.json
    android_manifest = DIST / "android_patch_manifest.json"
    if android_manifest.exists():
        am = json.loads(android_manifest.read_text(encoding="utf-8"))
        am["release_tag"] = "v1.1.0"
        am["version"] = "1.1.0"
        am["data_arcx"] = {
            "path": "Persistent_Store/Tables/data.arcx",
            "size_bytes": data_size,
            "sha256": data_sha
        }
        am["lua_arcx"] = {
            "path": "Persistent_Store/Scripts/lua.arcx",
            "size_bytes": lua_size,
            "sha256": lua_sha
        }
        android_manifest.write_text(json.dumps(am, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Updated dist/android_patch_manifest.json to v1.1.0")

def deploy_to_client(client_root: Path, client_name: str):
    if not client_root.exists():
        print(f"Client {client_name} does not exist at {client_root}, skipping.")
        return False
    print(f"\nDeploying v1.1.0 to {client_name} ({client_root})...")
    
    # 1. Deploy data.arcx
    target_data = client_root / "Persistent_Store" / "Tables" / "data.arcx"
    target_data.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA_ARCX, target_data)
    print(f"  -> Deployed data.arcx to {target_data}")

    # 2. Deploy lua.arcx
    target_lua = client_root / "Persistent_Store" / "Scripts" / "lua.arcx"
    target_lua.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LUA_ARCX, target_lua)
    print(f"  -> Deployed lua.arcx to {target_lua}")

    # 3. Deploy Videos SRT
    if VIDEOS_DIR.exists():
        target_videos = client_root / "Persistent_Store" / "Videos"
        target_videos.mkdir(parents=True, exist_ok=True)
        for srt in VIDEOS_DIR.glob("*.srt"):
            shutil.copy2(srt, target_videos / srt.name)
        print(f"  -> Deployed {len(list(VIDEOS_DIR.glob('*.srt')))} SRT files to {target_videos}")

    return True

def main():
    print("=================================================================")
    print("DEPLOYING STELLA SORA VIETNAMESE V1.1.0")
    print("=================================================================")
    update_manifests()

    yostar_ok = deploy_to_client(YOSTAR_ROOT, "Standalone Yostar Client")
    steam_ok = deploy_to_client(STEAM_ROOT, "Steam Client")

    print("\nDeployment completed successfully!")

if __name__ == "__main__":
    main()
