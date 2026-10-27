#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync android_patch_manifest.json and SHA256SUMS.txt after removing banner 20162.
"""

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
MANIFEST_PATH = DIST_DIR / "android_patch_manifest.json"
ZIP_PATH = DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip"
SHA_FILE = DIST_DIR / "SHA256SUMS.txt"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== ĐỒNG BỘ ANDROID_PATCH_MANIFEST.JSON SAU KHI XOÁ BANNER 20162 ===")
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        m = json.load(f)

    zip_size = ZIP_PATH.stat().st_size
    zip_sha = sha256_file(ZIP_PATH)

    m["version"] = "1.0.5"
    m["package_zip"] = {
        "filename": "StellaSora_Android_AssetBundles_VI.zip",
        "url": "https://github.com/doubleD1302/AmeeVH/releases/download/v1.0.5/StellaSora_Android_AssetBundles_VI.zip",
        "size": zip_size,
        "sha256": zip_sha,
    }

    data_p = DIST_DIR / "data_patched_vi.arcx"
    lua_p = DIST_DIR / "lua_patched_vi.arcx"

    files = [
        {
            "path": "Persistent_Store/Tables/data.arcx",
            "size": data_p.stat().st_size,
            "sha256": sha256_file(data_p),
            "asset_platform": "android",
            "url": "https://github.com/doubleD1302/AmeeVH/releases/download/v1.0.5/data_patched_vi.arcx",
        },
        {
            "path": "Persistent_Store/Scripts/lua.arcx",
            "size": lua_p.stat().st_size,
            "sha256": sha256_file(lua_p),
            "asset_platform": "android",
            "url": "https://github.com/doubleD1302/AmeeVH/releases/download/v1.0.5/lua_patched_vi.arcx",
        },
    ]

    bundle_dir = DIST_DIR / "android_AssetBundles"
    bundles = sorted(bundle_dir.glob("*.unity3d"))
    for b in bundles:
        files.append({
            "path": f"Persistent_Store/AssetBundles/{b.name}",
            "size": b.stat().st_size,
            "sha256": sha256_file(b),
            "asset_platform": "android",
        })

    m["files"] = files
    m["total_size"] = sum(f["size"] for f in files)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)

    print(f"Updated {MANIFEST_PATH.name}!")
    print(f"Total files: {len(files)} (92 bundles + 2 arcx)")
    print(f"ZIP size: {zip_size:,} bytes")
    print(f"ZIP SHA256: {zip_sha}")

    # Update SHA256SUMS.txt
    release_assets = [
        DIST_DIR / "StellaSora-Windows_v1.0.5.exe",
        DIST_DIR / "StellaSora-Android_v1.0.4.apk",
        DIST_DIR / "patch_manifest.json",
        MANIFEST_PATH,
        DIST_DIR / "android_localadb_launcher.json",
        data_p,
        lua_p,
        DIST_DIR / "StellaSora_AssetBundles_VI.zip",
        ZIP_PATH,
    ]

    sha_lines = []
    for f in release_assets:
        if f.exists():
            sha_lines.append(f"{sha256_file(f)}  {f.name}")

    SHA_FILE.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    print("Updated SHA256SUMS.txt successfully!")


if __name__ == "__main__":
    main()
