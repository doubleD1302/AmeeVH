#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload updated Android package ZIP, manifest, and SHA256SUMS to GitHub Release v1.0.0.
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
ZIP_FILE = DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip"
MANIFEST_PATH = DIST_DIR / "android_patch_manifest.json"
SHA_FILE = DIST_DIR / "SHA256SUMS.txt"

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.4"


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()


def get_release(headers: dict) -> dict:
    url = f"https://api.github.com/repos/{REPO}/releases"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    rel = next((r for r in releases if r.get("tag_name") == TAG), None)
    if not rel:
        raise RuntimeError(f"Release {TAG} not found in {REPO}")
    return rel


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
    print("=== TẢI LÊN GÓI ANDROID MỚI LÊN GITHUB RELEASE V1.0.0 ===")
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
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}

    # 1. Upload StellaSora_Android_AssetBundles_VI.zip
    if ZIP_FILE.exists():
        zip_bytes = ZIP_FILE.read_bytes()
        print(f"\n1. Tải lên {ZIP_FILE.name} ({len(zip_bytes)/(1024*1024):.2f} MB)...")
        upload_single_asset(rel, ZIP_FILE.name, zip_bytes, "application/zip", headers, existing_assets)

    # 2. Upload android_patch_manifest.json
    if MANIFEST_PATH.exists():
        manifest_bytes = MANIFEST_PATH.read_bytes()
        print(f"\n2. Tải lên {MANIFEST_PATH.name} ({len(manifest_bytes):,} bytes)...")
        # refresh assets
        rel = get_release(headers)
        existing_assets = {a["name"]: a for a in rel.get("assets", [])}
        upload_single_asset(rel, MANIFEST_PATH.name, manifest_bytes, "application/json", headers, existing_assets)

    # 3. Update & Upload SHA256SUMS.txt
    print("\n3. Cập nhật và tải lên SHA256SUMS.txt...")
    data_arcx = DIST_DIR / "data_patched_vi.arcx"
    lua_arcx = DIST_DIR / "lua_patched_vi.arcx"
    pc_zip = DIST_DIR / "StellaSora_AssetBundles_VI.zip"
    
    sha_lines = [
        f"{sha256_file(data_arcx)}  data_patched_vi.arcx",
        f"{sha256_file(lua_arcx)}  lua_patched_vi.arcx",
        f"{sha256_file(MANIFEST_PATH)}  android_patch_manifest.json",
        f"{sha256_file(ZIP_FILE)}  StellaSora_Android_AssetBundles_VI.zip",
    ]
    if pc_zip.exists():
        sha_lines.append(f"{sha256_file(pc_zip)}  StellaSora_AssetBundles_VI.zip")

    sha_content = "\n".join(sha_lines) + "\n"
    SHA_FILE.write_text(sha_content, encoding="utf-8")
    
    rel = get_release(headers)
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}
    upload_single_asset(rel, SHA_FILE.name, sha_content.encode("utf-8"), "text/plain", headers, existing_assets)

    print("\n=== HOÀN TẤT ĐỒNG BỘ RELEASE V1.0.0 THÀNH CÔNG! ===")


if __name__ == "__main__":
    main()
