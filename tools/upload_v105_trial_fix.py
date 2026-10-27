#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload updated bundle zips, manifests, and SHA256SUMS to GitHub Release v1.0.5.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.5"

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

def get_release(headers: dict) -> dict:
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    rel = next((r for r in releases if r.get("tag_name") == TAG), None)
    if not rel:
        raise RuntimeError(f"Release {TAG} not found in {REPO}")
    return rel

def upload_single_asset(rel, aname: str, data: bytes, ctype: str, headers: dict):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    
    # Always refresh existing assets
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}
    if aname in existing_assets:
        aid = existing_assets[aname]["id"]
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
    print("=== TẢI LÊN CÁC TỆP CẬP NHẬT LÊN GITHUB RELEASE V1.0.5 ===")
    token = get_github_token()
    if not token:
        print("Lỗi: Không tìm thấy GitHub token.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    rel = get_release(headers)
    print(f"Release ID: {rel['id']}, Tag: {rel['tag_name']}")

    assets_to_upload = [
        ("StellaSora_Android_AssetBundles_VI.zip", "application/zip"),
        ("StellaSora_AssetBundles_VI.zip", "application/zip"),
        ("android_patch_manifest.json", "application/json"),
        ("patch_manifest.json", "application/json"),
        ("SHA256SUMS.txt", "text/plain"),
    ]

    for fname, ctype in assets_to_upload:
        p = DIST_DIR / fname
        if not p.exists():
            print(f"Bỏ qua {fname} (không tồn tại)")
            continue
        data = p.read_bytes()
        print(f"\nĐang tải lên {fname} ({len(data):,} bytes)...")
        rel = get_release(headers)
        upload_single_asset(rel, fname, data, ctype, headers)

    print("\n✓ Hoàn tất tải lên toàn bộ assets cho v1.0.5!")

if __name__ == "__main__":
    main()
