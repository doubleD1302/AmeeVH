#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revert CharSkin_ArtText_11703_lang in icon-4.en.unity3d back to pristine English
for both PC and Android, repack zips, update manifests, update SHA256SUMS.txt,
and synchronize release assets to GitHub v1.0.5.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

from PIL import Image, ImageChops
import UnityPy
from UnityPy.streams import EndianBinaryReader

PROJECT_ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
DIST_DIR = PROJECT_ROOT / "dist"
DIST_BUNDLES_DIR = DIST_DIR / "AssetBundles"
ANDROID_BUNDLES_DIR = DIST_DIR / "android_AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
BACKUP_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
ANDROID_SRC_DIR = PROJECT_ROOT / "work" / "android_pipeline" / "source_bundles"

PC_ZIP_OUTPUT = DIST_DIR / "StellaSora_AssetBundles_VI.zip"
ANDROID_ZIP_OUTPUT = DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip"
PC_MANIFEST_PATH = DIST_DIR / "patch_manifest.json"
ANDROID_MANIFEST_PATH = DIST_DIR / "android_patch_manifest.json"
SHA_FILE = DIST_DIR / "SHA256SUMS.txt"

YOSTAR_PS = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")
STEAM_PS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
STEAM_IR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.5"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()


def get_github_token() -> str:
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line[9:]
    return ""


def step1_patch_pc_icon4() -> bytes:
    print("\n=== BƯỚC 1: PHỤC HỒI TEXTURE GỐC TIẾNG ANH CHO PC (icon-4.en.unity3d) ===")
    pc_backup = BACKUP_DIR / "icon-4.en.unity3d"
    pc_dist = DIST_BUNDLES_DIR / "icon-4.en.unity3d"
    assert pc_backup.exists(), f"Không tìm thấy backup PC: {pc_backup}"
    assert pc_dist.exists(), f"Không tìm thấy dist PC: {pc_dist}"

    bak_env = UnityPy.load(str(pc_backup))
    dist_env = UnityPy.load(str(pc_dist))

    # Identify target Texture2D parameters
    target_tex = None
    for obj in bak_env.objects:
        if obj.type.name == "Texture2D" and obj.read().m_Name == "CharSkin_ArtText_11703_lang":
            target_tex = obj.read()
            break
    assert target_tex is not None, "Không tìm thấy CharSkin_ArtText_11703_lang trong backup"

    offset = int(target_tex.m_StreamData.offset)
    length = int(target_tex.m_StreamData.size)
    print(f"  + Texture: {target_tex.m_Name}, offset={offset}, size={length}, format={target_tex.m_TextureFormat}")

    bak_res_name = [k for k in bak_env.file.files.keys() if k.endswith(".resS")][0]
    dist_res_name = [k for k in dist_env.file.files.keys() if k.endswith(".resS")][0]

    bak_bytes = bytes(bak_env.file.files[bak_res_name].bytes)
    dist_node = dist_env.file.files[dist_res_name]
    dist_bytes = bytearray(bytes(dist_node.bytes))

    # Replace bytes with pristine English original
    dist_bytes[offset : offset + length] = bak_bytes[offset : offset + length]

    reader = EndianBinaryReader(bytes(dist_bytes))
    reader.flags = dist_node.flags
    dist_env.file.files[dist_res_name] = reader
    patched_pc_bytes = dist_env.file.save(packer="original")

    # Readback verification
    print("  + Xác thực readback giải mã PC...")
    v_env = UnityPy.load(patched_pc_bytes)
    v_img = None
    for obj in v_env.objects:
        if obj.type.name == "Texture2D" and obj.read().m_Name == "CharSkin_ArtText_11703_lang":
            v_img = obj.read().image
            break
    assert v_img is not None, "Readback PC thất bại: không trích xuất được ảnh"
    
    bak_img = target_tex.image
    diff = ImageChops.difference(v_img.convert("RGBA"), bak_img.convert("RGBA"))
    assert diff.getbbox() is None, f"Readback PC không khớp ảnh gốc: diff={diff.getbbox()}"
    print(f"  ✓ PC readback thành công! Bbox difference = None (100% khớp tiếng Anh gốc)")

    # Save to PC dist and staging
    (DIST_BUNDLES_DIR / "icon-4.en.unity3d").write_bytes(patched_pc_bytes)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    (STAGING_DIR / "icon-4.en.unity3d").write_bytes(patched_pc_bytes)
    print(f"  ✓ Đã lưu dist/AssetBundles/icon-4.en.unity3d ({len(patched_pc_bytes):,} bytes)")

    # Sync to local game installations
    for dest_dir, desc in [
        (YOSTAR_PS, "Yostar Persistent_Store"),
        (STEAM_PS, "Steam Persistent_Store"),
        (STEAM_IR, "Steam InstallResource"),
    ]:
        if dest_dir.exists():
            dest_file = dest_dir / "icon-4.en.unity3d"
            try:
                dest_file.write_bytes(patched_pc_bytes)
                print(f"  ✓ Đồng bộ thành công tới: {desc}")
            except Exception as e:
                print(f"  ⚠️ Lưu ý: Không thể ghi vào {desc} ({e})")

    return patched_pc_bytes


def step2_repack_pc_zip():
    print("\n=== BƯỚC 2: ĐÓNG GÓI LẠI StellaSora_AssetBundles_VI.zip (PC) ===")
    t0 = time.time()
    with zipfile.ZipFile(PC_ZIP_OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        bundles = sorted(DIST_BUNDLES_DIR.glob("*.en.unity3d"))
        for p in bundles:
            zf.write(p, arcname=p.name)
    elapsed = time.time() - t0
    print(f"  ✓ Đã đóng gói {len(bundles)} bundles vào {PC_ZIP_OUTPUT.name} ({PC_ZIP_OUTPUT.stat().st_size:,} bytes, {elapsed:.1f}s)")


def step3_patch_android_icon4() -> bytes:
    print("\n=== BƯỚC 3: PHỤC HỒI TEXTURE GỐC TIẾNG ANH CHO ANDROID (icon-4.en.unity3d) ===")
    android_src = ANDROID_SRC_DIR / "icon-4.en.unity3d"
    android_dist = ANDROID_BUNDLES_DIR / "icon-4.en.unity3d"
    assert android_src.exists(), f"Không tìm thấy source Android: {android_src}"
    assert android_dist.exists(), f"Không tìm thấy dist Android: {android_dist}"

    src_env = UnityPy.load(str(android_src))
    dist_env = UnityPy.load(str(android_dist))

    # Identify target Texture2D parameters
    target_tex = None
    for obj in src_env.objects:
        if obj.type.name == "Texture2D" and obj.read().m_Name == "CharSkin_ArtText_11703_lang":
            target_tex = obj.read()
            break
    assert target_tex is not None, "Không tìm thấy CharSkin_ArtText_11703_lang trong Android source"

    offset = int(target_tex.m_StreamData.offset)
    length = int(target_tex.m_StreamData.size)
    print(f"  + Android Texture: {target_tex.m_Name}, offset={offset}, size={length}, format={target_tex.m_TextureFormat}")

    src_res_name = [k for k in src_env.file.files.keys() if k.endswith(".resS")][0]
    dist_res_name = [k for k in dist_env.file.files.keys() if k.endswith(".resS")][0]

    src_bytes = bytes(src_env.file.files[src_res_name].bytes)
    dist_node = dist_env.file.files[dist_res_name]
    dist_bytes = bytearray(bytes(dist_node.bytes))

    # Replace bytes with pristine English ASTC original
    dist_bytes[offset : offset + length] = src_bytes[offset : offset + length]

    reader = EndianBinaryReader(bytes(dist_bytes))
    reader.flags = dist_node.flags
    dist_env.file.files[dist_res_name] = reader
    patched_android_bytes = dist_env.file.save(packer="original")

    # Readback verification
    print("  + Xác thực readback giải mã Android ASTC...")
    v_env = UnityPy.load(patched_android_bytes)
    v_img = None
    for obj in v_env.objects:
        if obj.type.name == "Texture2D" and obj.read().m_Name == "CharSkin_ArtText_11703_lang":
            v_img = obj.read().image
            break
    assert v_img is not None, "Readback Android thất bại: không trích xuất được ảnh"

    src_img = target_tex.image
    diff = ImageChops.difference(v_img.convert("RGBA"), src_img.convert("RGBA"))
    assert diff.getbbox() is None, f"Readback Android không khớp ảnh gốc: diff={diff.getbbox()}"
    print(f"  ✓ Android readback thành công! Bbox difference = None (100% khớp tiếng Anh gốc)")

    # Save to Android dist
    android_dist.write_bytes(patched_android_bytes)
    print(f"  ✓ Đã lưu dist/android_AssetBundles/icon-4.en.unity3d ({len(patched_android_bytes):,} bytes)")

    return patched_android_bytes


def step4_repack_android_zip():
    print("\n=== BƯỚC 4: ĐÓNG GÓI LẠI StellaSora_Android_AssetBundles_VI.zip (Android) ===")
    t0 = time.time()
    with zipfile.ZipFile(ANDROID_ZIP_OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        bundles = sorted(ANDROID_BUNDLES_DIR.glob("*.en.unity3d"))
        for p in bundles:
            zf.write(p, arcname=f"Persistent_Store/AssetBundles/{p.name}")
    elapsed = time.time() - t0
    print(f"  ✓ Đã đóng gói {len(bundles)} bundles vào {ANDROID_ZIP_OUTPUT.name} ({ANDROID_ZIP_OUTPUT.stat().st_size:,} bytes, {elapsed:.1f}s)")


def step5_update_manifests():
    print("\n=== BƯỚC 5: CẬP NHẬT BẢNG KÊ MANIFEST PC & ANDROID ===")
    
    # 1. Update PC patch_manifest.json
    pc_icon4 = DIST_BUNDLES_DIR / "icon-4.en.unity3d"
    pc_icon4_sha = sha256_file(pc_icon4)
    pc_icon4_size = pc_icon4.stat().st_size
    pc_zip_sha = sha256_file(PC_ZIP_OUTPUT)
    pc_zip_size = PC_ZIP_OUTPUT.stat().st_size

    with open(PC_MANIFEST_PATH, "r", encoding="utf-8") as f:
        pc_m = json.load(f)

    if "bundles" in pc_m and "icon-4.en.unity3d" in pc_m["bundles"]:
        pc_m["bundles"]["icon-4.en.unity3d"]["patched_sha256"] = pc_icon4_sha
        pc_m["bundles"]["icon-4.en.unity3d"]["size_bytes"] = pc_icon4_size
        if "textures_patched" in pc_m["bundles"]["icon-4.en.unity3d"]:
            pc_m["bundles"]["icon-4.en.unity3d"]["textures_patched"] -= 1

    if "files" in pc_m and isinstance(pc_m["files"], dict):
        if "Persistent_Store/AssetBundles/icon-4.en.unity3d" in pc_m["files"]:
            pc_m["files"]["Persistent_Store/AssetBundles/icon-4.en.unity3d"]["sha256"] = pc_icon4_sha
            pc_m["files"]["Persistent_Store/AssetBundles/icon-4.en.unity3d"]["size"] = pc_icon4_size

    if "package_zip" in pc_m and isinstance(pc_m["package_zip"], dict):
        pc_m["package_zip"]["sha256"] = pc_zip_sha
        pc_m["package_zip"]["size_bytes"] = pc_zip_size

    pc_m["asset_bundles_package_sha256"] = pc_zip_sha
    pc_m["asset_bundles_package_size"] = pc_zip_size
    pc_m["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(PC_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(pc_m, f, indent=2, ensure_ascii=False)
    print("  ✓ Đã cập nhật dist/patch_manifest.json")

    # 2. Update Android android_patch_manifest.json
    android_icon4 = ANDROID_BUNDLES_DIR / "icon-4.en.unity3d"
    android_icon4_sha = sha256_file(android_icon4)
    android_icon4_size = android_icon4.stat().st_size
    android_zip_sha = sha256_file(ANDROID_ZIP_OUTPUT)
    android_zip_size = ANDROID_ZIP_OUTPUT.stat().st_size

    with open(ANDROID_MANIFEST_PATH, "r", encoding="utf-8") as f:
        android_m = json.load(f)

    if "package_zip" in android_m and isinstance(android_m["package_zip"], dict):
        android_m["package_zip"]["sha256"] = android_zip_sha
        android_m["package_zip"]["size"] = android_zip_size

    for f_entry in android_m.get("files", []):
        if f_entry.get("path") == "Persistent_Store/AssetBundles/icon-4.en.unity3d":
            f_entry["sha256"] = android_icon4_sha
            f_entry["size"] = android_icon4_size
            break

    android_m["total_size"] = sum(f["size"] for f in android_m.get("files", []))

    with open(ANDROID_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(android_m, f, indent=2, ensure_ascii=False)
    print("  ✓ Đã cập nhật dist/android_patch_manifest.json")

    # 3. Update dist/SHA256SUMS.txt
    release_assets = [
        DIST_DIR / "StellaSora-Windows_v1.0.5.exe",
        DIST_DIR / "StellaSora-Android_v1.0.4.apk",
        PC_MANIFEST_PATH,
        ANDROID_MANIFEST_PATH,
        DIST_DIR / "android_localadb_launcher.json",
        DIST_DIR / "data_patched_vi.arcx",
        DIST_DIR / "lua_patched_vi.arcx",
        PC_ZIP_OUTPUT,
        ANDROID_ZIP_OUTPUT,
    ]

    sha_lines = []
    for p in release_assets:
        if p.exists():
            sha_lines.append(f"{sha256_file(p)}  {p.name}")

    SHA_FILE.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    print(f"  ✓ Đã cập nhật {SHA_FILE.name} với {len(sha_lines)} tệp phát hành")


def step6_upload_to_github():
    print(f"\n=== BƯỚC 6: TẢI ĐÈ TỆP CẬP NHẬT LÊN GITHUB RELEASE {TAG} ===")
    token = get_github_token()
    if not token:
        print("  ⚠️ Không tìm thấy GitHub token từ git credential. Bỏ qua tải lên GitHub.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "StellaSora-Release-Bot",
    }

    # Fetch release
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))

    rel = None
    for r in releases:
        if r.get("tag_name") == TAG:
            rel = r
            break
    assert rel is not None, f"Không tìm thấy release {TAG} trên repo {REPO}"
    print(f"  + Tìm thấy GitHub Release: {TAG} (id: {rel['id']})")

    # Get existing assets
    assets_url = rel["assets_url"]
    with urllib.request.urlopen(urllib.request.Request(assets_url, headers=headers)) as resp:
        existing = {a["name"]: a for a in json.loads(resp.read().decode("utf-8"))}

    files_to_sync = [
        (PC_ZIP_OUTPUT, "application/zip"),
        (ANDROID_ZIP_OUTPUT, "application/zip"),
        (PC_MANIFEST_PATH, "application/json"),
        (ANDROID_MANIFEST_PATH, "application/json"),
        (SHA_FILE, "text/plain"),
    ]

    upload_url_tmpl = rel["upload_url"].split("{")[0]

    for p, ctype in files_to_sync:
        data = p.read_bytes()
        aname = p.name

        if aname in existing:
            aid = existing[aname]["id"]
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/assets/{aid}",
                headers=headers,
                method="DELETE",
            )
            try:
                urllib.request.urlopen(del_req)
                print(f"  + Đã xoá bản cũ: {aname} (id: {aid})")
            except Exception as e:
                print(f"  ⚠️ Lưu ý khi xoá {aname}: {e}")

        # Upload
        up_url = f"{upload_url_tmpl}?name={aname}"
        up_req = urllib.request.Request(
            up_url,
            data=data,
            headers={
                **headers,
                "Content-Type": ctype,
                "Content-Length": str(len(data)),
            },
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(up_req, timeout=300) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    print(f"  ✓ Đã tải lên GitHub Release thành công: {aname} ({len(data):,} bytes)")
                    break
            except Exception as e:
                print(f"  ⚠️ Thử lại {attempt+1}/4 cho {aname}: {e}")
                if attempt == 3:
                    raise
                time.sleep(2 + attempt * 2)


def main():
    print("=" * 75)
    print("GỠ BANNER 'DIỄU HÀNH HỘI MAY MẮN' (CharSkin_ArtText_11703_lang) TRÊN PC & ANDROID")
    print("=" * 75)
    t0 = time.time()

    step1_patch_pc_icon4()
    step2_repack_pc_zip()
    step3_patch_android_icon4()
    step4_repack_android_zip()
    step5_update_manifests()
    step6_upload_to_github()

    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print(f"🎉 HOÀN THÀNH TẤT CẢ CÁC BƯỚC TRONG {elapsed:.1f} GIÂY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
