#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create GitHub Release v1.0.8 and upload all assets according to docs/GITHUB_RELEASE_RULES.md.
"""

from pathlib import Path
import hashlib
import json
import re
import subprocess
import time
import urllib.request
import urllib.error

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.8"

# STRICT TITLE AND BODY VALIDATION PER docs/GITHUB_RELEASE_RULES.md
RELEASE_TITLE = "1.0.8"
RELEASE_NOTES = """- Khắc phục triệt để lỗi xưng hô "anh/chị" hướng tới nhân vật chính, loại bỏ hoàn toàn tình trạng gọi nhầm khi chơi nhân vật nữ.
- Chuẩn hóa đồng bộ danh xưng và thuật ngữ trong toàn bộ cốt truyện, lời thoại hẹn hò, kỹ năng, đĩa nhạc và giao diện.
- Cập nhật Launcher PC (v1.0.8) và Android APK (v1.0.8) hỗ trợ tự động tải và cài đặt trực tiếp trong ứng dụng."""

def validate_release():
    title = RELEASE_TITLE.strip()
    body = RELEASE_NOTES.strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", title):
        raise ValueError("Tiêu đề chỉ được chứa số phiên bản, ví dụ 0.1.2.")
    word_count = len(body.split())
    if word_count == 0 or word_count > 100:
        raise ValueError(f"Mô tả có {word_count} từ, không hợp lệ (phải từ 1 đến 100 từ).")
    print(f"Validated release title: '{title}', body word count: {word_count}")

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
    url = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Found existing release {TAG}")
            rel = json.loads(resp.read().decode("utf-8"))
            # Update title & body to ensure compliance
            update_url = f"https://api.github.com/repos/{REPO}/releases/{rel['id']}"
            update_payload = {
                "name": RELEASE_TITLE,
                "body": RELEASE_NOTES,
            }
            update_req = urllib.request.Request(
                update_url,
                data=json.dumps(update_payload).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(update_req) as up_resp:
                return json.loads(up_resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Release {TAG} not found, creating new release...")
        else:
            raise

    # Create release
    create_url = f"https://api.github.com/repos/{REPO}/releases"
    payload = {
        "tag_name": TAG,
        "target_commitish": "main",
        "name": RELEASE_TITLE,
        "body": RELEASE_NOTES,
        "draft": False,
        "prerelease": False,
    }
    create_req = urllib.request.Request(
        create_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(create_req) as resp:
        rel = json.loads(resp.read().decode("utf-8"))
        print(f"✓ Created release {TAG} (id: {rel['id']})")
        return rel

def upload_asset(rel: dict, file_path: Path, headers: dict, existing_assets: dict):
    aname = file_path.name
    data = file_path.read_bytes()
    size = len(data)
    upload_url_tmpl = rel["upload_url"].split("{")[0]

    force_reupload = {
        "android_patch_manifest.json",
        "patch_manifest.json",
        "android_localadb_launcher.json",
        "SHA256SUMS.txt",
        "data_patched_vi.arcx",
        "lua_patched_vi.arcx",
    }

    if aname in existing_assets:
        e_info = existing_assets[aname]
        if aname not in force_reupload and e_info.get("size") == size:
            print(f"✓ {aname} already exists with matching size ({size:,} bytes), skipping upload.")
            return e_info.get("browser_download_url")
        # Delete stale
        aid = e_info["id"]
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/assets/{aid}",
            headers=headers,
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"Deleted stale {aname} (id: {aid})")
        except Exception as exc:
            print(f"Notice deleting {aname}: {exc}")

    ctype = "application/octet-stream"
    if aname.endswith(".json") or aname.endswith(".txt"):
        ctype = "text/plain; charset=utf-8"
    elif aname.endswith(".zip"):
        ctype = "application/zip"
    elif aname.endswith(".exe"):
        ctype = "application/vnd.microsoft.portable-executable"
    elif aname.endswith(".apk"):
        ctype = "application/vnd.android.package-archive"

    upload_url = f"{upload_url_tmpl}?name={aname}"
    up_req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            **headers,
            "Content-Type": ctype,
            "Content-Length": str(size),
        },
        method="POST",
    )
    for attempt in range(1, 5):
        try:
            print(f"Uploading {aname} ({size:,} bytes) [attempt {attempt}]...")
            with urllib.request.urlopen(up_req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                print(f"✓ Successfully uploaded {aname}")
                return res.get("browser_download_url")
        except Exception as exc:
            print(f"  Attempt {attempt} failed: {exc}")
            if attempt == 4:
                raise
            time.sleep(3)

def main():
    validate_release()
    token = get_github_token()
    assert token, "Could not get GitHub token from git credentials."
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Antigravity-Release-Deployer",
    }

    rel = get_or_create_release(headers)
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}

    assets_to_upload = [
        DIST_DIR / f"StellaSora-Windows_{TAG}.exe",
        DIST_DIR / f"StellaSora-Android_{TAG}.apk",
        DIST_DIR / "android_localadb_launcher.json",
        DIST_DIR / "patch_manifest.json",
        DIST_DIR / "android_patch_manifest.json",
        DIST_DIR / "data_patched_vi.arcx",
        DIST_DIR / "lua_patched_vi.arcx",
        DIST_DIR / "StellaSora_AssetBundles_VI.zip",
        DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip",
        DIST_DIR / "SHA256SUMS.txt",
    ]

    for p in assets_to_upload:
        assert p.is_file(), f"Missing asset: {p}"
        upload_asset(rel, p, headers, existing_assets)

    print("\n" + "=" * 60)
    print(f"🎉 TẤT CẢ ASSETS CHO RELEASE {TAG} ĐÃ ĐƯỢC UPLOAD VÀ ĐỒNG BỘ THÀNH CÔNG!")
    print(f"Title: {RELEASE_TITLE}")
    print(f"Body: {RELEASE_NOTES}")
    print("=" * 60)

if __name__ == "__main__":
    main()
