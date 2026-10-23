#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package offline bundle StellaSora_Launcher_PC.zip for Client Release v0.9.7.
Includes:
- StellaSora_Launcher.exe (v0.9.7)
- data_patched_vi.arcx (2,670 Data table lines)
- lua_patched_vi.arcx (12,554 Lua story & dialogue lines, 66,224 replaced)
- patch_manifest.json (v0.9.7)
- All 63 AssetBundles (842 textures)
"""

import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
DIST_DIR = ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / "StellaSora_Launcher_PC.zip"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== PACKAGING StellaSora_Launcher_PC.zip FOR v0.9.7 ===")
    t0 = time.time()
    
    exe_file = DIST_DIR / "StellaSora_Launcher.exe"
    data_file = DIST_DIR / "data_patched_vi.arcx"
    lua_file = DIST_DIR / "lua_patched_vi.arcx"
    manifest_file = DIST_DIR / "patch_manifest.json"
    bundles_dir = DIST_DIR / "AssetBundles"
    
    assert exe_file.exists(), "Missing StellaSora_Launcher.exe"
    assert data_file.exists(), "Missing data_patched_vi.arcx"
    assert lua_file.exists(), "Missing lua_patched_vi.arcx"
    assert manifest_file.exists(), "Missing patch_manifest.json"
    
    bundles = sorted(bundles_dir.glob("*.en.unity3d"))
    assert len(bundles) == 63, f"Expected 63 bundles, found {len(bundles)}"
    
    print(f"Adding core files and 63 AssetBundles into {OUTPUT_ZIP.name}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Root files
        zf.write(exe_file, arcname="StellaSora_Launcher.exe")
        zf.write(data_file, arcname="data_patched_vi.arcx")
        zf.write(lua_file, arcname="lua_patched_vi.arcx")
        zf.write(manifest_file, arcname="patch_manifest.json")
        
        # dist/ prefixed copies for launcher relative paths
        zf.write(data_file, arcname="dist/data_patched_vi.arcx")
        zf.write(lua_file, arcname="dist/lua_patched_vi.arcx")
        zf.write(manifest_file, arcname="dist/patch_manifest.json")
        
        for bf in bundles:
            zf.write(bf, arcname=f"dist/AssetBundles/{bf.name}")
            
    elapsed = time.time() - t0
    zip_size = OUTPUT_ZIP.stat().st_size
    zip_sha = sha256_file(OUTPUT_ZIP)
    
    print(f"\nSUCCESS! Created {OUTPUT_ZIP} in {elapsed:.2f}s:")
    print(f"  Size: {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
    print(f"  SHA256: {zip_sha}")

if __name__ == "__main__":
    main()
