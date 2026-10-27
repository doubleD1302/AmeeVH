#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up loose .unity3d assets from GitHub Release v1.0.0 and upload updated core packages.
Uses ThreadPoolExecutor for fast concurrent deletion and robust timeouts.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import time
import urllib.request

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"

def get_github_token() -> str:
    p = subprocess.Popen(
        ["git", "-C", str(PROJECT_ROOT), "credential", "fill"],
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

def get_release(headers: dict) -> dict:
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    rel = next((r for r in releases if r.get("tag_name") == TAG), None)
    if not rel:
        raise RuntimeError(f"Release {TAG} not found in {REPO}")
    return rel

def delete_asset(aid: int, aname: str, headers: dict):
    del_req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/assets/{aid}",
        headers=headers,
        method="DELETE",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(del_req, timeout=15):
                pass
            print(f"  [Xóa thành công] {aname}", flush=True)
            return True
        except Exception as e:
            if attempt == 2:
                print(f"  [Lỗi xóa] {aname}: {e}", flush=True)
                return False
            time.sleep(1)

def upload_single_asset(rel, file_path: Path, ctype: str, headers: dict):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    aname = file_path.name
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}

    if aname in existing_assets:
        asset_info = existing_assets[aname]
        if asset_info.get("size") == file_path.stat().st_size:
            print(f"  [Bỏ qua] {aname} (kích thước trùng khớp {file_path.stat().st_size:,} bytes)", flush=True)
            return
        aid = asset_info["id"]
        delete_asset(aid, aname, headers)

    upload_url = f"{upload_url_tmpl}?name={aname}"
    data = file_path.read_bytes()
    print(f"  [Tải lên] {aname} ({len(data) / 1024 / 1024:.2f} MB)...", flush=True)
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
            with urllib.request.urlopen(up_req, timeout=180) as resp:
                up_res = json.loads(resp.read().decode("utf-8"))
                print(f"  -> Thành công: {aname}", flush=True)
                return
        except Exception as e:
            print(f"  [Thử lại {attempt+1}] Lỗi tải {aname}: {e}", flush=True)
            time.sleep(2)
    raise RuntimeError(f"Failed to upload {aname}")

def main():
    print("=== DỌN DẸP TỆP RỜI VÀ GỘP GÓI TRÊN GITHUB RELEASE V1.0.0 ===", flush=True)
    token = get_github_token()
    if not token:
        print("Lỗi: Không lấy được token GitHub.", flush=True)
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    rel = get_release(headers)
    print(f"Release: {rel['tag_name']} (id: {rel['id']}), Tổng số asset hiện tại: {len(rel['assets'])}", flush=True)

    # 1. Tìm và xóa toàn bộ các tệp rời rạc .unity3d bằng ThreadPoolExecutor
    unity3d_assets = [a for a in rel.get("assets", []) if a["name"].endswith(".unity3d")]
    print(f"\n1. Đang xóa song song {len(unity3d_assets)} tệp .unity3d rời rạc...", flush=True)
    if unity3d_assets:
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(delete_asset, a["id"], a["name"], headers) for a in unity3d_assets]
            for f in as_completed(futures):
                f.result()

    # 2. Cập nhật các tệp cốt lõi lên Release
    print("\n2. Tải lên / cập nhật các gói cốt lõi chuẩn hóa...", flush=True)
    rel = get_release(headers)

    assets_to_sync = [
        (DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip", "application/zip"),
        (DIST_DIR / "StellaSora-Android_v1.0.0.apk", "application/vnd.android.package-archive"),
        (DIST_DIR / "android_patch_manifest.json", "application/json"),
        (DIST_DIR / "android_localadb_launcher.json", "application/json"),
        (DIST_DIR / "SHA256SUMS.txt", "text/plain"),
    ]

    for fpath, ctype in assets_to_sync:
        if fpath.exists():
            upload_single_asset(rel, fpath, ctype, headers)
        else:
            print(f"Cảnh báo: Không tìm thấy {fpath}", flush=True)

    # 3. Kiểm tra danh sách asset cuối cùng
    rel = get_release(headers)
    final_assets = rel.get("assets", [])
    print(f"\n=== HOÀN TẤT DỌN DẸP GITHUB RELEASE ===", flush=True)
    print(f"Tổng số tệp sau khi gộp và tinh giản: {len(final_assets)}", flush=True)
    for a in sorted(final_assets, key=lambda x: x["name"]):
        mb = a["size"] / 1024 / 1024
        print(f"  * {a['name']:<40} {mb:>8.2f} MB  (id: {a['id']})", flush=True)

if __name__ == "__main__":
    main()
