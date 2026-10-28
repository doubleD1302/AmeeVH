#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification suite for Stella Sora Seamless Update Assurance.
Checks all 6 gates before release publishing.
"""

from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== KIỂM TRA CHỈ TIÊU BẢO ĐẢM TỰ ĐỘNG CẬP NHẬT TRỰC TIẾP (SEAMLESS UPDATE GATES) ===")
    errors = []

    # Gate 1: versionCode of APK > release hiện tại (v1.0.7 was versionCode 9)
    gradle_file = ROOT / "android" / "app" / "build.gradle"
    gradle_txt = gradle_file.read_text(encoding="utf-8")
    vc_match = re.search(r"versionCode\s+(\d+)", gradle_txt)
    if not vc_match or int(vc_match.group(1)) <= 9:
        errors.append(f"Gate 1 thất bại: versionCode phải > 9, tìm thấy {vc_match.group(1) if vc_match else 'None'}")
    else:
        print(f"✓ Gate 1: versionCode = {vc_match.group(1)} (> 9)")

    # Gate 2: LAUNCHER_VERSION của PC == "1.0.8"
    cfg_file = ROOT / "launcher" / "core" / "config.py"
    cfg_txt = cfg_file.read_text(encoding="utf-8")
    lv_match = re.search(r'LAUNCHER_VERSION\s*=\s*"([^"]+)"', cfg_txt)
    if not lv_match or lv_match.group(1) != "1.0.8":
        errors.append(f"Gate 2 thất bại: LAUNCHER_VERSION phải là 1.0.8, tìm thấy {lv_match.group(1) if lv_match else 'None'}")
    else:
        print(f"✓ Gate 2: LAUNCHER_VERSION = {lv_match.group(1)}")

    # Gate 3: Helper của PC launcher chứa taskkill và target.rename
    updater_file = ROOT / "launcher" / "core" / "self_update.py"
    check_code = updater_file.read_text(encoding="utf-8") if updater_file.exists() else ""
    if "taskkill" not in check_code or "target.rename" not in check_code:
        errors.append("Gate 3 thất bại: Cơ chế tự cập nhật PC thiếu taskkill hoặc rename logic")
    else:
        print("✓ Gate 3: PC updater có đầy đủ cơ chế ngắt tiến trình cha và rename an toàn")

    # Gate 4: android_localadb_launcher.json có SHA256 và size khớp 100% với APK phát hành
    apk_file = DIST / "StellaSora-Android_v1.0.8.apk"
    localadb_file = DIST / "android_localadb_launcher.json"
    if not apk_file.exists() or not localadb_file.exists():
        errors.append("Gate 4 thất bại: Không tìm thấy APK hoặc android_localadb_launcher.json")
    else:
        apk_sha = sha256_file(apk_file)
        apk_size = apk_file.stat().st_size
        meta = json.loads(localadb_file.read_text(encoding="utf-8"))
        if meta.get("sha256") != apk_sha or meta.get("size") != apk_size:
            errors.append(f"Gate 4 thất bại: Metadata không khớp (meta sha={meta.get('sha256')}, apk sha={apk_sha})")
        else:
            print(f"✓ Gate 4: android_localadb_launcher.json khớp 100% (size={apk_size:,}, sha={apk_sha[:16]}...)")

    # Gate 5: android_patch_manifest.json và patch_manifest.json chứa '*' trong resource_version
    pc_man_file = DIST / "patch_manifest.json"
    and_man_file = DIST / "android_patch_manifest.json"
    pc_man = json.loads(pc_man_file.read_text(encoding="utf-8"))
    and_man = json.loads(and_man_file.read_text(encoding="utf-8"))
    if "*" not in pc_man.get("resource_version", ""):
        errors.append("Gate 5 thất bại: patch_manifest.json thiếu wildcard '*' trong resource_version")
    if "*" not in and_man.get("resource_version", ""):
        errors.append("Gate 5 thất bại: android_patch_manifest.json thiếu wildcard '*' trong resource_version")
    if "*" in pc_man.get("resource_version", "") and "*" in and_man.get("resource_version", ""):
        print("✓ Gate 5: Cả 2 manifests đều có wildcard '*' trong resource_version")

    # Gate 6: android_patch_manifest.json tuân thủ ChannelClient
    cc_ok = True
    if and_man.get("platform") != "android":
        errors.append("Gate 6: platform != 'android'")
        cc_ok = False
    if and_man.get("game_package") != "com.YoStarEN.StellaSora":
        errors.append("Gate 6: game_package != 'com.YoStarEN.StellaSora'")
        cc_ok = False
    for f in and_man.get("files", []):
        if f.get("asset_platform") != "android":
            errors.append(f"Gate 6: file {f.get('path')} thiếu asset_platform='android'")
            cc_ok = False
            break
    if cc_ok:
        print("✓ Gate 6: android_patch_manifest.json tuân thủ nghiêm ngặt hợp đồng ChannelClient")

    if errors:
        print("\n❌ CÓ LỖI XẢY RA TRONG KIỂM TRA:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n=======================================================")
    print("🎉 TẤT CẢ 6 CỔNG KIỂM TRA BẢO ĐẢM TỰ ĐỘNG CẬP NHẬT ĐÃ ĐẠT 100%!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
