#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload updated data_patched_vi.arcx, lua_patched_vi.arcx, manifests and checksums to GitHub Release v1.0.5.
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
    
    # Refresh release assets
    rel_refresh = get_release(headers)
    existing_assets = {a["name"]: a for a in rel_refresh.get("assets", [])}
    
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
            time.sleep(1)
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
                print(f"SUCCESS: Uploaded {aname} ({len(data):,} bytes)")
                return dl_url
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {aname}: {e}")
            if attempt == 3:
                raise
            time.sleep(2)

def main():
    token = get_github_token()
    if not token:
        print("ERROR: GitHub token not found.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    rel = get_release(headers)
    print(f"Target Release: {rel['tag_name']} (ID: {rel['id']})")

    files_to_upload = [
        ("data_patched_vi.arcx", DIST_DIR / "data_patched_vi.arcx", "application/octet-stream"),
        ("lua_patched_vi.arcx", DIST_DIR / "lua_patched_vi.arcx", "application/octet-stream"),
        ("patch_manifest.json", DIST_DIR / "patch_manifest.json", "application/json"),
        ("android_patch_manifest.json", DIST_DIR / "android_patch_manifest.json", "application/json"),
        ("SHA256SUMS.txt", DIST_DIR / "SHA256SUMS.txt", "text/plain"),
    ]

    for aname, fpath, ctype in files_to_upload:
        if not fpath.exists():
            print(f"File not found: {fpath}")
            continue
        data = fpath.read_bytes()
        print(f"\nUploading {aname} ({len(data):,} bytes)...")
        upload_single_asset(rel, aname, data, ctype, headers)

    print("\n=== ALL V1.0.5 ASSETS SYNCED TO GITHUB RELEASE SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
