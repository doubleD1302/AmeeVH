#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Stella Sora Vietnamese Localization to v1.3.0 (Compatible with Game Patch 2.1.0).
- Integrates all 1,124 approved Data Tables translations from 2.1.0 localization QA review.
- Repacks data.arcx preserving all engine/binary schemas via arcx_adapter.repack_archive.
- Updates patch_manifest.json and android_patch_manifest.json.
"""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.arcx_adapter import (
    ArcxArchive,
    repack_archive,
    xxtea_decrypt,
    xxtea_encrypt,
    XXTEA_KEY,
)

def update_data_arcx():
    print("\n--- REPACKING DATA.ARCX (2.1.0) ---")
    status_path = ROOT / "work" / "runs" / "localize_202_210_20261113_r01" / "TABLES_001_1124_REVIEW_STATUS.json"
    with open(status_path, "r", encoding="utf-8") as f:
        st = json.load(f)

    # Collect all 1124 translations mapped by entry hash hex and key
    translations_by_hash = {}
    total_loaded = 0
    for p in st["packets"]:
        res_path = ROOT / p["result_path"].replace("\\\\", "/")
        if not res_path.exists():
            res_path = Path(p["result_path"].replace("\\\\", "/"))
        with open(res_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        for d in res["decisions"]:
            cid = d["id"]  # 2.1.0:data:0x0ca3f0a82aa87471:/ActivityDoubleQuest.107001.1
            parts = cid.split(":")
            h_hex = parts[2].lower()
            key = parts[3].lstrip("/")
            val = d.get("approved_text", d.get("text_vi", ""))
            if h_hex not in translations_by_hash:
                translations_by_hash[h_hex] = {}
            translations_by_hash[h_hex][key] = val
            total_loaded += 1

    print(f"Loaded {total_loaded} translations across {len(translations_by_hash)} table entries.")

    vi_arcx_path = ROOT / "dist" / "data_patched_vi.arcx"
    output_path = ROOT / "dist" / "data_patched_vi.arcx"

    vi_arc = ArcxArchive(vi_arcx_path)
    vi_raw = vi_arcx_path.read_bytes()

    staging_dir = ROOT / "work" / "staging_data_210"
    entries_dir = staging_dir / "entries"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    entries_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "archive_name": "data.arcx",
        "version": vi_arc.version,
        "flag": vi_arc.flag,
        "entry_count": vi_arc.entry_count,
        "payload_decrypted": False,
        "entries": [],
    }

    json_count = 0
    binary_count = 0
    patched_keys_count = 0

    for e in vi_arc.entries:
        h = e["hash"]
        h_hex = e["hash_hex"].lower()
        entry_bytes = vi_arc.extract_entry(e, vi_raw)
        payload = xxtea_decrypt(entry_bytes, XXTEA_KEY)

        is_json = False
        data_json = None
        try:
            data_json = json.loads(payload.decode("utf-8"))
            is_json = isinstance(data_json, dict)
        except Exception:
            pass

        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        fpath = entries_dir / fname

        if is_json:
            json_count += 1
            if h_hex in translations_by_hash:
                for k, vi_str in translations_by_hash[h_hex].items():
                    data_json[k] = vi_str
                    patched_keys_count += 1

            new_payload_bytes = json.dumps(data_json, ensure_ascii=False, indent=2).encode("utf-8")
            enc_payload = xxtea_encrypt(new_payload_bytes, XXTEA_KEY)
            fpath.write_bytes(enc_payload)
            final_size = len(enc_payload)
        else:
            binary_count += 1
            fpath.write_bytes(entry_bytes)
            final_size = len(entry_bytes)

        manifest["entries"].append({
            "index": e["index"],
            "hash": h,
            "hash_hex": e["hash_hex"],
            "filename": fname,
            "origin_size": final_size,
            "payload_size": final_size,
        })

    manifest_file = staging_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Total entries: {len(manifest['entries'])} (JSON: {json_count}, Binary: {binary_count})")
    print(f"Total 2.1.0 keys patched into data.arcx: {patched_keys_count}")

    t0 = time.time()
    repack_archive(staging_dir, output_path, encrypt_payload=False)
    dur = time.time() - t0
    new_size = output_path.stat().st_size
    with open(output_path, "rb") as f:
        new_sha = hashlib.sha256(f.read()).hexdigest()
    print(f"✓ Successfully repacked {output_path} ({new_size:,} bytes, sha256: {new_sha}) in {dur:.2f}s")
    return output_path, new_sha, new_size

def update_manifests(data_sha, data_size):
    print("\n--- UPDATING PATCH MANIFESTS (v1.3.0 / Game 2.1.0) ---")
    dist = ROOT / "dist"
    
    # 1. PC patch_manifest.json
    pc_manifest_path = dist / "patch_manifest.json"
    with open(pc_manifest_path, "r", encoding="utf-8") as f:
        pc_manifest = json.load(f)
    
    pc_manifest["release_tag"] = "v1.3.0"
    pc_manifest["version"] = "1.3.0"
    pc_manifest["client_game_version"] = "2.1.0"
    pc_manifest["resource_version"] = "2610201624, 2610211918, 2610211926, 2610291554, 2611131554, *"
    
    with open(pc_manifest_path, "w", encoding="utf-8") as f:
        json.dump(pc_manifest, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated {pc_manifest_path}")

    # 2. Android android_patch_manifest.json
    android_manifest_path = dist / "android_patch_manifest.json"
    with open(android_manifest_path, "r", encoding="utf-8") as f:
        android_manifest = json.load(f)
        
    android_manifest["client_game_version"] = "2.1.0"
    android_manifest["resource_version"] = "2610201624, 2610211918, 2610211926, 2610291554, 2611131554, *"
    android_manifest["version"] = "1.3.0"
    
    # Update data.arcx file info in android manifest
    for file_info in android_manifest.get("files", []):
        if "data.arcx" in file_info.get("path", ""):
            file_info["size"] = data_size
            file_info["sha256"] = data_sha
            file_info["url"] = f"https://github.com/doubleD1302/AmeeVH/releases/download/v1.3.0/data_patched_vi.arcx"
            print(f"  -> Updated android data.arcx file record to size {data_size}, sha256 {data_sha}")
        elif "lua.arcx" in file_info.get("path", ""):
            file_info["url"] = f"https://github.com/doubleD1302/AmeeVH/releases/download/v1.3.0/lua_patched_vi.arcx"
            
    with open(android_manifest_path, "w", encoding="utf-8") as f:
        json.dump(android_manifest, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated {android_manifest_path}")

if __name__ == "__main__":
    out_path, d_sha, d_size = update_data_arcx()
    update_manifests(d_sha, d_size)
    print("\n✓ ALL DATA 2.1.0 REPACKING COMPLETE!")
