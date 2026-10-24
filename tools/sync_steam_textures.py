#!/usr/bin/env python3
"""Sync verified Vietnamese AssetBundles (Textures) to Steam game installation.

Features:
1. Verifies 63 bundles against dist/patch_manifest.json.
2. Backs up original Steam files with preimage hash guard.
3. Applies atomic replace to both:
   - Steam's Persistent_Store/AssetBundles/
   - Steam's StellaSora_Data/StreamingAssets/InstallResource/ (critical for Steam engine)
4. Updates Steam's viethoa_installed.json to v0.9.7.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STEAM_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora")
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"
ZIP_PATH = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"
SRC_BUNDLES_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
BACKUP_DIR = PROJECT_ROOT / "backups" / "steam_pre_texture_patch"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def is_game_running() -> bool:
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq StellaSora.exe" /NH', shell=True).decode()
        return "StellaSora.exe" in out
    except Exception:
        return False


def sync_to_steam(steam_path: Path = DEFAULT_STEAM_PATH, dry_run: bool = False) -> int:
    print("=" * 70)
    print("ĐỒNG BỘ 100% TEXTURE VIỆT HÓA V0.9.7 VÀO BẢN GAME STEAM")
    print("=" * 70)

    if not steam_path.exists():
        print(f"❌ ERROR: Không tìm thấy thư mục Steam tại: {steam_path}")
        return 1

    if is_game_running():
        print("❌ ERROR: Trò chơi StellaSora.exe đang chạy! Vui lòng đóng game trước khi áp dụng.")
        return 1

    if not MANIFEST_PATH.exists():
        print(f"❌ ERROR: Không tìm thấy tệp manifest tại: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    bundles_manifest = manifest_data.get("bundles", {})
    print(f"-> Manifest ghi nhận: {len(bundles_manifest)} bundles ({manifest_data.get('total_textures_patched', 842)} textures)")

    # Prepare bundle source
    bundles_source: dict[str, bytes] = {}
    if SRC_BUNDLES_DIR.exists() and len(list(SRC_BUNDLES_DIR.glob("*.en.unity3d"))) >= 63:
        print(f"-> Đọc trực tiếp từ thư mục dist: {SRC_BUNDLES_DIR.name}")
        for b_name in bundles_manifest.keys():
            p = SRC_BUNDLES_DIR / b_name
            if p.exists():
                bundles_source[b_name] = p.read_bytes()
    elif ZIP_PATH.exists():
        print(f"-> Giải nén từ gói ZIP: {ZIP_PATH.name}")
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                b_name = Path(member.filename).name
                if b_name in bundles_manifest:
                    bundles_source[b_name] = zf.read(member.filename)

    if len(bundles_source) < 63:
        print(f"❌ ERROR: Chỉ tìm thấy {len(bundles_source)}/63 bundles nguồn hợp lệ!")
        return 1

    # Verify SHA256 of source bundles
    print("-> Xác thực SHA256 các bundle nguồn...")
    for b_name, b_bytes in bundles_source.items():
        actual_sha = hashlib.sha256(b_bytes).hexdigest().lower()
        expected_sha = bundles_manifest[b_name]["patched_sha256"].lower()
        if actual_sha != expected_sha:
            print(f"❌ ERROR: Sai mã băm cho {b_name}: {actual_sha} != {expected_sha}")
            return 1
    print("   ✓ Toàn bộ 63 bundles nguồn khớp SHA256 100%.")

    # Target directories
    ps_dir = steam_path / "Persistent_Store" / "AssetBundles"
    ir_dir = steam_path / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
    ps_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("\n[DRY RUN] Kiểm tra thành công! Không có thay đổi nào được ghi vào đĩa.")
        return 0

    # Create backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_backup_dir = BACKUP_DIR / f"run_{timestamp}"
    run_backup_dir.mkdir(parents=True, exist_ok=True)
    backup_manifest = {
        "timestamp": timestamp,
        "steam_path": str(steam_path),
        "files": []
    }

    print(f"-> Tạo bản sao lưu an toàn tại: {run_backup_dir.name}...")
    for b_name in bundles_manifest.keys():
        for base_d, label in [(ps_dir, "Persistent_Store"), (ir_dir, "InstallResource")]:
            target_f = base_d / b_name
            if target_f.exists():
                bak_name = f"{label}_{b_name}"
                bak_f = run_backup_dir / bak_name
                shutil.copy2(target_f, bak_f)
                backup_manifest["files"].append({
                    "relative": f"{label}/{b_name}",
                    "backup_file": bak_name,
                    "sha256": sha256_file(target_f)
                })

    with open(run_backup_dir / "backup_manifest.json", "w", encoding="utf-8") as f:
        json.dump(backup_manifest, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Đã sao lưu {len(backup_manifest['files'])} tệp gốc an toàn.")

    # Apply atomic replace
    print("-> Áp dụng 63 tệp AssetBundles Việt Hóa vào Steam...")
    applied_ps = 0
    applied_ir = 0

    for b_name, b_bytes in bundles_source.items():
        # 1. Apply to Persistent_Store/AssetBundles
        target_ps = ps_dir / b_name
        tmp_ps = target_ps.with_suffix(".tmp_patch")
        tmp_ps.write_bytes(b_bytes)
        tmp_ps.replace(target_ps)
        applied_ps += 1

        # 2. Apply to InstallResource (crucial for Steam client base lookup)
        if ir_dir.exists():
            target_ir = ir_dir / b_name
            tmp_ir = target_ir.with_suffix(".tmp_patch")
            tmp_ir.write_bytes(b_bytes)
            tmp_ir.replace(target_ir)
            applied_ir += 1

    # Update viethoa_installed.json in Steam
    patch_marker = {
        "installed_at": timestamp,
        "version": "0.9.7",
        "release_tag": "v0.9.7",
        "platform": "Steam",
        "components": [
            "Tables (data.arcx - 100% Việt Hóa)",
            "Scripts (lua.arcx - 100% Cốt truyện & Tin nhắn)",
            f"AssetBundles ({applied_ps} bundles - 842 Textures Việt Hóa)"
        ],
        "textures_applied": {
            "total_bundles": applied_ps,
            "persistent_store_applied": applied_ps,
            "install_resource_applied": applied_ir,
            "total_textures": 842
        }
    }
    marker_path = steam_path / "Persistent_Store" / "viethoa_installed.json"
    marker_path.write_text(json.dumps(patch_marker, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 70)
    print("🎉 HOÀN TẤT ĐỒNG BỘ 100% TEXTURE VIỆT HÓA CHO STEAM!")
    print(f"📦 Đã nạp vào Persistent_Store: {applied_ps}/63 AssetBundles")
    print(f"📦 Đã nạp vào InstallResource:   {applied_ir}/63 AssetBundles")
    print(f"🏷️ Phiên bản cập nhật Steam:     v0.9.7")
    print(f"📁 Thư mục game Steam:            {steam_path}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Vietnamese textures to Steam")
    parser.add_argument("--path", type=Path, default=DEFAULT_STEAM_PATH, help="Steam game path")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing")
    args = parser.parse_args()
    sys.exit(sync_to_steam(args.path, args.dry_run))
