#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload updated patch_manifest.json and StellaSora_AssetBundles_VI.zip to GitHub Release v1.0.0."""

import json
from pathlib import Path
import subprocess
import time
import urllib.request

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

def upload_asset_to_release(rel, file_path: Path, ctype: str, headers: dict, repo: str):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    existing_assets = {a["name"]: a["id"] for a in rel.get("assets", [])}
    aname = file_path.name

    if aname in existing_assets:
        aid = existing_assets[aname]
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/assets/{aid}",
            headers=headers,
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"Deleted old asset {aname} (id: {aid})")
        except Exception as e:
            print(f"Could not delete old asset {aname}: {e}")

    file_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"Uploading {aname} ({file_mb:.2f} MB)...")
    upload_url = f"{upload_url_tmpl}?name={aname}"
    data = file_path.read_bytes()
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
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(up_req, timeout=300) as resp:
                up_res = json.loads(resp.read().decode("utf-8"))
                print(f"Uploaded {aname} -> {up_res.get('browser_download_url')}")
                break
        except Exception as e:
            print(f"Upload attempt {attempt + 1} failed for {aname}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(3)

def main():
    root = Path(__file__).parent.parent
    token = get_github_token()
    if not token:
        print("Error: Could not retrieve GitHub token")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    repo = "doubleD1302/AmeeVH"
    tag = "v1.0.0"

    check_req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases", headers=headers
    )
    with urllib.request.urlopen(check_req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))

    rel = next((r for r in releases if r.get("tag_name") == tag), None)
    if not rel:
        print(f"Error: Release {tag} not found!")
        return

    print(f"Found release: {rel['tag_name']} (id: {rel['id']})")
    dist = root / "dist"

    assets_to_upload = [
        (dist / "patch_manifest.json", "application/json"),
        (dist / "StellaSora_AssetBundles_VI.zip", "application/zip"),
        (dist / "SHA256SUMS.txt", "text/plain"),
    ]

    for fpath, ctype in assets_to_upload:
        if fpath.exists():
            upload_asset_to_release(rel, fpath, ctype, headers, repo)
        else:
            print(f"Error: File not found: {fpath}")

    print("\n=== HOÀN TẤT ĐỒNG BỘ TÀI NGUYÊN V1.0.0 LÊN GITHUB ===")

if __name__ == "__main__":
    main()
