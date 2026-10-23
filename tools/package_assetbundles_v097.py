#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package all 63 AssetBundles into StellaSora_AssetBundles_VI.zip
and update dist/patch_manifest.json with exact hashes and metadata for v0.9.7.
"""

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
DIST_BUNDLES_DIR = ROOT / "dist" / "AssetBundles"
OUTPUT_ZIP = ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"
MANIFEST_PATH = ROOT / "dist" / "patch_manifest.json"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== PACKAGING 63 ASSETBUNDLES FOR v0.9.7 ===")
    bundle_files = sorted(DIST_BUNDLES_DIR.glob("*.unity3d"))
    print(f"Found {len(bundle_files)} AssetBundles in {DIST_BUNDLES_DIR}")
    assert len(bundle_files) == 63, f"Expected 63 bundles, found {len(bundle_files)}!"

    print(f"Creating {OUTPUT_ZIP.name}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for bf in bundle_files:
            zf.write(bf, arcname=bf.name)
            
    zip_size = OUTPUT_ZIP.stat().st_size
    zip_sha = sha256_file(OUTPUT_ZIP)
    print(f"Created {OUTPUT_ZIP} ({zip_size:,} bytes, {zip_size / (1024*1024):.2f} MB)")
    print(f"SHA256: {zip_sha}")

    # Update manifest
    print(f"\nUpdating {MANIFEST_PATH.name}...")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}
    manifest["release_tag"] = "v0.9.7"
    manifest["total_bundles"] = 63
    manifest["total_textures_patched"] = 842
    
    bundles_dict = manifest.setdefault("bundles", {})
    for bf in bundle_files:
        b_sha = sha256_file(bf)
        b_size = bf.stat().st_size
        b_info = bundles_dict.setdefault(bf.name, {})
        b_info["patched_sha256"] = b_sha
        b_info["size_bytes"] = b_size
        b_info["relative_path"] = f"Persistent_Store/AssetBundles/{bf.name}"

    manifest["package_zip"] = {
        "filename": "StellaSora_AssetBundles_VI.zip",
        "size_bytes": zip_size,
        "sha256": zip_sha,
        "total_bundles": 63
    }
    manifest["asset_bundles_package_sha256"] = zip_sha
    manifest["asset_bundles_package_size"] = zip_size

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {MANIFEST_PATH} successfully!")

if __name__ == "__main__":
    main()
