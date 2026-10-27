#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create GitHub Release v1.0.2 and upload release assets to doubleD1302/AmeeVH.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.2"
NAME = "Stella Sora Việt Hóa v1.0.2 — Bản cập nhật Đồ Họa 95 AssetBundles & Banner Toàn Diện"
BODY = """## 🌟 Stella Sora Việt Hóa v1.0.2

Bản cập nhật chính thức v1.0.2 nâng cấp toàn diện hệ thống hình ảnh, giao diện và gói tài nguyên Android/PC.

### ✨ Điểm nổi bật trong bản v1.0.2:
- **Tích hợp trọn vẹn 95 AssetBundles Android ASTC**: Nâng cấp toàn bộ hệ thống đồ họa nạp vào game trên thiết bị di động chuẩn GPU ASTC nguyên bản.
- **28 Banner Gacha Cover hoàn chỉnh**: Bổ sung đầy đủ banner Kỷ niệm 1 năm (*Một Năm Sao Sáng, Một Cuộc Tái Ngộ Định Mệnh*), banner nhân vật tiêu điểm (*Chiêu Mộ Đặc Biệt*), banner đĩa ký ức (*Khắc Ấn Âm Vang*) cùng toàn bộ 25 banner gacha khác.
- **Trang phục & Cửa hàng Mall**: Hiển thị trọn bộ 12 chữ thư pháp trang phục nhân vật và 17 poster giới thiệu trang phục lữ khách trong thương thành.
- **Truyện tranh màn hình chờ (Loading Comics)**: Tích hợp đầy đủ các tập truyện 4 ô đã được dịch thuật và biên tập mỹ thuật.
- **Gói nén ZIP tinh giản duy nhất**: Gom toàn bộ 95 AssetBundles vào `StellaSora_Android_AssetBundles_VI.zip` (78.58 MB), loại bỏ triệt để tình trạng phân mảnh tệp lẻ và tối ưu hóa 100% tốc độ cài đặt qua APK.
- **Cập nhật APK Local ADB Launcher (v1.0.2, versionCode 6)**: Tối ưu cơ chế kiểm tra môi trường nhà phát triển và đồng bộ tài nguyên tức thì.
"""


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


def get_or_create_release(headers: dict) -> dict:
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    
    for r in releases:
        if r.get("tag_name") == TAG:
            print(f"Found existing release for {TAG} (id: {r['id']})")
            return r

    # Create new release
    print(f"Creating new release {TAG} in {REPO}...")
    create_payload = json.dumps({
        "tag_name": TAG,
        "target_commitish": "main",
        "name": NAME,
        "body": BODY,
        "draft": False,
        "prerelease": False
    }).encode("utf-8")
    
    create_req = urllib.request.Request(
        url,
        data=create_payload,
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(create_req) as resp:
        new_rel = json.loads(resp.read().decode("utf-8"))
    print(f"Created release {TAG} (id: {new_rel['id']})")
    return new_rel


def upload_single_asset(rel, aname: str, data: bytes, ctype: str, headers: dict, existing_assets: dict):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    
    if aname in existing_assets:
        asset_info = existing_assets[aname]
        if asset_info.get("size") == len(data):
            print(f"Skipping {aname} (size matches: {len(data):,} bytes)")
            return f"https://github.com/{REPO}/releases/download/{TAG}/{aname}"
        aid = asset_info["id"]
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/assets/{aid}",
            headers=headers,
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"Deleted outdated {aname} (id: {aid})")
        except Exception as e:
            print(f"Notice deleting {aname}: {e}")

    upload_url = f"{upload_url_tmpl}?name={aname}"
    up_req = urllib.request.Request(
        upload_url,
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
                up_res = json.loads(resp.read().decode("utf-8"))
                dl_url = up_res.get("browser_download_url")
                print(f"Uploaded {aname} ({len(data):,} bytes)")
                return dl_url
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {aname}: {e}")
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 2)


def main():
    print(f"=== TẠO VÀ ĐỒNG BỘ RELEASE {TAG} LÊN GITHUB ===")
    token = get_github_token()
    if not token:
        print("Lỗi: Không tìm thấy GitHub token.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    rel = get_or_create_release(headers)
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}

    assets_to_upload = [
        ("StellaSora-Android_v1.0.2.apk", "application/vnd.android.package-archive"),
        ("StellaSora-Windows_v1.0.2.exe", "application/octet-stream"),
        ("StellaSora_Android_AssetBundles_VI.zip", "application/zip"),
        ("StellaSora_AssetBundles_VI.zip", "application/zip"),
        ("android_patch_manifest.json", "application/json"),
        ("android_localadb_launcher.json", "application/json"),
        ("data_patched_vi.arcx", "application/octet-stream"),
        ("lua_patched_vi.arcx", "application/octet-stream"),
        ("SHA256SUMS.txt", "text/plain"),
    ]

    for fname, ctype in assets_to_upload:
        p = DIST_DIR / fname
        if not p.exists():
            print(f"[SKIP] Not found: {fname}")
            continue
        data = p.read_bytes()
        print(f"\nĐang tải lên {fname} ({len(data):,} bytes)...")
        # refresh assets map
        rel = get_or_create_release(headers)
        existing_assets = {a["name"]: a for a in rel.get("assets", [])}
        upload_single_asset(rel, fname, data, ctype, headers, existing_assets)

    print(f"\n=== HOÀN TẤT ĐỒNG BỘ TOÀN BỘ TÀI NGUYÊN LÊN RELEASE {TAG}! ===")


if __name__ == "__main__":
    main()
