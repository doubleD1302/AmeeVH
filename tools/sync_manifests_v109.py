#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate and synchronize manifests and SHA256SUMS.txt for Release v1.0.9.
Ensures exact matching sizes, hashes, and asset bundle structures.
"""

from pathlib import Path
import hashlib
import json
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
VERSION = "1.0.9"
TAG = "v1.0.9"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()

def update_manifests():
    print(f"=== ĐỒNG BỘ MANIFEST CHO PHIÊN BẢN {TAG} ===")
    
    data_p = DIST_DIR / "data_patched_vi.arcx"
    lua_p = DIST_DIR / "lua_patched_vi.arcx"
    pc_zip = DIST_DIR / "StellaSora_AssetBundles_VI.zip"
    and_zip = DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip"

    assert data_p.exists() and lua_p.exists()
    assert pc_zip.exists() and and_zip.exists()

    data_size = data_p.stat().st_size
    data_sha = sha256_file(data_p)
    lua_size = lua_p.stat().st_size
    lua_sha = sha256_file(lua_p)
    pc_zip_size = pc_zip.stat().st_size
    pc_zip_sha = sha256_file(pc_zip)
    and_zip_size = and_zip.stat().st_size
    and_zip_sha = sha256_file(and_zip)

    # 1. PC MANIFEST
    pc_manifest_path = DIST_DIR / "patch_manifest.json"
    pc_bundles_dir = DIST_DIR / "AssetBundles"
    pc_bundles = sorted(pc_bundles_dir.glob("*.unity3d"))

    bundles_map = {}
    files_map = {
        "Persistent_Store/Tables/data.arcx": {
            "source": "data_patched_vi.arcx",
            "sha256": data_sha,
            "size": data_size,
        },
        "Persistent_Store/Scripts/lua.arcx": {
            "source": "lua_patched_vi.arcx",
            "sha256": lua_sha,
            "size": lua_size,
        },
    }

    for b in pc_bundles:
        b_sha = sha256_file(b)
        b_size = b.stat().st_size
        bundles_map[b.name] = {
            "patched_sha256": b_sha,
            "size_bytes": b_size,
            "textures_patched": 1,
        }
        files_map[f"Persistent_Store/AssetBundles/{b.name}"] = {
            "source": f"AssetBundles/{b.name}",
            "sha256": b_sha,
            "size": b_size,
        }

    pc_manifest = {
        "release_tag": TAG,
        "version": VERSION,
        "client_game_version": "2.0.0",
        "resource_version": "2610201624, 2610211918, 2610211926, *",
        "total_bundles": len(pc_bundles),
        "total_textures_patched": 420,
        "bundles": bundles_map,
        "package_zip": {
            "filename": "StellaSora_AssetBundles_VI.zip",
            "url": f"https://github.com/doubleD1302/AmeeVH/releases/download/{TAG}/StellaSora_AssetBundles_VI.zip",
            "size": pc_zip_size,
            "sha256": pc_zip_sha,
        },
        "files": files_map,
        "platform": "windows",
    }

    pc_manifest_path.write_text(json.dumps(pc_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✓ Đã cập nhật {pc_manifest_path.name} ({len(pc_bundles)} bundles, total files: {len(files_map)})")

    # 2. ANDROID MANIFEST
    and_manifest_path = DIST_DIR / "android_patch_manifest.json"
    and_bundles_dir = DIST_DIR / "android_AssetBundles"
    and_bundles = sorted(and_bundles_dir.glob("*.unity3d"))

    and_files = [
        {
            "path": "Persistent_Store/Tables/data.arcx",
            "size": data_size,
            "sha256": data_sha,
            "asset_platform": "android",
            "url": f"https://github.com/doubleD1302/AmeeVH/releases/download/{TAG}/data_patched_vi.arcx",
        },
        {
            "path": "Persistent_Store/Scripts/lua.arcx",
            "size": lua_size,
            "sha256": lua_sha,
            "asset_platform": "android",
            "url": f"https://github.com/doubleD1302/AmeeVH/releases/download/{TAG}/lua_patched_vi.arcx",
        },
    ]

    for b in and_bundles:
        b_sha = sha256_file(b)
        b_size = b.stat().st_size
        and_files.append({
            "path": f"Persistent_Store/AssetBundles/{b.name}",
            "size": b_size,
            "sha256": b_sha,
            "asset_platform": "android",
        })

    and_manifest = {
        "platform": "android",
        "game_package": "com.YoStarEN.StellaSora",
        "client_game_version": "2.0.0",
        "resource_version": "2610201624, 2610211918, 2610211926, *",
        "version": VERSION,
        "total_size": sum(f["size"] for f in and_files),
        "package_zip": {
            "filename": "StellaSora_Android_AssetBundles_VI.zip",
            "url": f"https://github.com/doubleD1302/AmeeVH/releases/download/{TAG}/StellaSora_Android_AssetBundles_VI.zip",
            "size": and_zip_size,
            "sha256": and_zip_sha,
        },
        "files": and_files,
    }

    and_manifest_path.write_text(json.dumps(and_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✓ Đã cập nhật {and_manifest_path.name} ({len(and_bundles)} bundles, total files: {len(and_files)})")

    # 3. ANDROID LOCAL ADB LAUNCHER METADATA
    localadb_path = DIST_DIR / "android_localadb_launcher.json"
    apk_path = DIST_DIR / f"StellaSora-Android_{TAG}.apk"
    if apk_path.exists():
        apk_sha = sha256_file(apk_path)
        apk_size = apk_path.stat().st_size
        localadb_meta = {
            "platform": "android",
            "variant": "localadb",
            "application_id": "com.stellasora.viethoa.localadb",
            "version_name": VERSION,
            "version_code": 11,
            "apk_name": f"StellaSora-Android_{TAG}.apk",
            "apk_url": f"https://github.com/doubleD1302/AmeeVH/releases/download/{TAG}/StellaSora-Android_{TAG}.apk",
            "size": apk_size,
            "sha256": apk_sha,
            "signing_cert_sha256": "21a38b89d9a315aee7028d25324fe4fd30ff40c97d4708310ae43ba670d74cd2",
        }
        localadb_path.write_text(json.dumps(localadb_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"✓ Đã cập nhật {localadb_path.name}")
    else:
        print(f"⚠️ {apk_path.name} chưa tồn tại, bỏ qua tạo localadb_meta")

    # 4. SHA256SUMS.txt
    release_files = [
        DIST_DIR / f"StellaSora-Windows_{TAG}.exe",
        DIST_DIR / f"StellaSora-Android_{TAG}.apk",
        localadb_path,
        pc_manifest_path,
        and_manifest_path,
        data_p,
        lua_p,
        pc_zip,
        and_zip,
    ]

    sha_lines = []
    for f in release_files:
        if f.exists():
            sha_lines.append(f"{sha256_file(f)}  {f.name}")
        else:
            print(f"⚠️ Missing release file: {f.name}")

    sums_path = DIST_DIR / "SHA256SUMS.txt"
    sums_path.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    print(f"✓ Đã cập nhật {sums_path.name} ({len(sha_lines)} assets)")
    for l in sha_lines:
        print(f"   {l}")

if __name__ == "__main__":
    update_manifests()
