#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create GitHub Release v1.0.5 and upload release assets to doubleD1302/AmeeVH.
Follows strictly docs/GITHUB_RELEASE_RULES.md.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.5"
TITLE = "1.0.5"
BODY = """- Cho phép launcher PC cài đặt bản Việt hoá trên mọi phiên bản game, không bị chặn do lệch phiên bản.
- Giữ nguyên cơ chế kiểm tra an toàn tệp và sao lưu dữ liệu gốc trước khi cài đặt.
- Nâng cấp phiên bản Launcher PC lên 1.0.5."""


def validate_release_text(title: str, body: str) -> tuple[str, str]:
    title = title.strip()
    body = body.strip()

    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", title):
        raise ValueError("Tiêu đề chỉ được chứa số phiên bản, ví dụ 0.1.2.")

    word_count = len(body.split())
    if word_count == 0:
        raise ValueError("Mô tả cần nêu nội dung cập nhật.")
    if word_count > 100:
        raise ValueError(f"Mô tả có {word_count} từ, vượt giới hạn 100 từ.")

    return title, body


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
    validate_release_text(TITLE, BODY)
    
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    
    for r in releases:
        if r.get("tag_name") == TAG:
            print(f"Found existing release for {TAG} (id: {r['id']})")
            # Update title and body if needed
            if r.get("name") != TITLE or r.get("body") != BODY:
                print(f"Updating release metadata for {TAG}...")
                patch_url = f"https://api.github.com/repos/{REPO}/releases/{r['id']}"
                patch_data = json.dumps({"name": TITLE, "body": BODY}).encode("utf-8")
                patch_req = urllib.request.Request(
                    patch_url,
                    data=patch_data,
                    headers={**headers, "Content-Type": "application/json"},
                    method="PATCH"
                )
                with urllib.request.urlopen(patch_req) as patch_resp:
                    r = json.loads(patch_resp.read().decode("utf-8"))
            return r

    # Create new release
    print(f"Creating new release {TAG} in {REPO}...")
    create_payload = json.dumps({
        "tag_name": TAG,
        "target_commitish": "main",
        "name": TITLE,
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
    print(f"=== PHÁT HÀNH GITHUB RELEASE {TAG} ({TITLE}) ===")
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
    print(f"Release ID: {rel['id']}, Tag: {rel['tag_name']}, Title: {rel['name']}")
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}

    asset_files = [
        ("StellaSora-Windows_v1.0.5.exe", "application/octet-stream"),
        ("StellaSora-Android_v1.0.4.apk", "application/vnd.android.package-archive"),
        ("patch_manifest.json", "application/json"),
        ("android_patch_manifest.json", "application/json"),
        ("android_localadb_launcher.json", "application/json"),
        ("data_patched_vi.arcx", "application/octet-stream"),
        ("lua_patched_vi.arcx", "application/octet-stream"),
        ("StellaSora_AssetBundles_VI.zip", "application/zip"),
        ("StellaSora_Android_AssetBundles_VI.zip", "application/zip"),
        ("SHA256SUMS.txt", "text/plain"),
    ]

    for fname, ctype in asset_files:
        fpath = DIST_DIR / fname
        if not fpath.exists():
            print(f"WARNING: File {fname} not found in dist/!")
            continue
        data = fpath.read_bytes()
        print(f"\nĐang tải lên {fname} ({len(data):,} bytes)...")
        # refresh release asset list
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/{rel['id']}", headers=headers)
        with urllib.request.urlopen(req) as resp:
            current_rel = json.loads(resp.read().decode("utf-8"))
        current_existing = {a["name"]: a for a in current_rel.get("assets", [])}
        upload_single_asset(current_rel, fname, data, ctype, headers, current_existing)

    # Re-verify release metadata on GitHub
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/{rel['id']}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        final_rel = json.loads(resp.read().decode("utf-8"))
    
    print("\n=== KIỂM CHỨNG BẢN PHÁT HÀNH TRÊN GITHUB ===")
    print(f"Tag: {final_rel.get('tag_name')}")
    print(f"Title: {final_rel.get('name')}")
    print(f"Word count: {len(final_rel.get('body', '').split())}")
    print(f"Total assets: {len(final_rel.get('assets', []))}")
    for a in final_rel.get('assets', []):
        print(f"  - {a.get('name')}: {a.get('size'):,} bytes")
    
    validate_release_text(final_rel.get("name", ""), final_rel.get("body", ""))
    print("\n✓ ĐÃ KIỂM TRA ĐẠT TOÀN BỘ QUY TẮC PHÁT HÀNH GITHUB!")


if __name__ == "__main__":
    main()
