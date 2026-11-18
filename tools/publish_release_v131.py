#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create or update GitHub Release v1.3.1 and upload/verify all 10 release assets per docs/GITHUB_RELEASE_RULES.md."""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
REPO = "doubleD1302/AmeeVH"
TAG = "v1.3.1"

RELEASE_TITLE = "1.3.1"
RELEASE_NOTES = """- Bản địa hóa lại cốt truyện Chương Mở đầu, Chương 1 và Chương 2 từ nguồn tiếng Anh theo văn phong Light Novel, đồng bộ toàn bộ bảng thuật ngữ.
- Đồng bộ dữ liệu Chương 9.5 và các chuỗi giao diện bản 2.1.0.
- Nâng cấp Launcher PC và Android lên v1.3.1: tự cập nhật an toàn khi khóa tệp, tự dò Steam/Yostar, tăng tốc Local ADB và hỗ trợ tải tiếp HTTP."""


def validate_release() -> None:
    title = RELEASE_TITLE.strip()
    body = RELEASE_NOTES.strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", title):
        raise ValueError("Tiêu đề chỉ được chứa số phiên bản, ví dụ 1.3.1.")
    word_count = len(body.split())
    if word_count == 0 or word_count > 100:
        raise ValueError(f"Mô tả có {word_count} từ, không hợp lệ (phải từ 1 đến 100 từ).")
    print(f"Validated release title={title!r}, word_count={word_count}")


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
            rel = json.loads(resp.read().decode("utf-8"))
            print(f"Found existing release {TAG} (id: {rel['id']})")
            update_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/{rel['id']}",
                data=json.dumps({"name": RELEASE_TITLE, "body": RELEASE_NOTES, "draft": False, "prerelease": False}).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(update_req) as up_resp:
                return json.loads(up_resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        print(f"Release {TAG} not found, creating...")

    payload = {
        "tag_name": TAG,
        "target_commitish": "main",
        "name": RELEASE_TITLE,
        "body": RELEASE_NOTES,
        "draft": False,
        "prerelease": False,
    }
    create_req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases",
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(create_req) as resp:
        rel = json.loads(resp.read().decode("utf-8"))
        print(f"Created release {TAG} (id: {rel['id']})")
        return rel


def upload_asset(rel: dict, file_path: Path, headers: dict, existing_assets: dict) -> str:
    aname = file_path.name
    data = file_path.read_bytes()
    size = len(data)
    upload_url_tmpl = rel["upload_url"].split("{")[0]

    if aname in existing_assets:
        e_info = existing_assets[aname]
        # Skip only immutable asset bundles if byte size matches; always refresh patched data/lua/manifests/binaries
        immutable_same_size = aname in {
            "StellaSora_AssetBundles_VI.zip",
            "StellaSora_Android_AssetBundles_VI.zip",
        }
        if immutable_same_size and e_info.get("size") == size:
            print(f"Keep {aname} (matching size {size:,} bytes)")
            return e_info.get("browser_download_url", "")
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/assets/{e_info['id']}",
            headers=headers,
            method="DELETE",
        )
        urllib.request.urlopen(del_req).read()
        print(f"Deleted stale {aname} (id: {e_info['id']})")

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
    for attempt in range(1, 5):
        try:
            print(f"Uploading {aname} ({size:,} bytes) [attempt {attempt}]...")
            up_req = urllib.request.Request(
                upload_url,
                data=data,
                headers={**headers, "Content-Type": ctype, "Content-Length": str(size)},
                method="POST",
            )
            with urllib.request.urlopen(up_req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                print(f"Uploaded {aname} -> {res.get('browser_download_url')}")
                return res.get("browser_download_url", "")
        except Exception as exc:
            print(f"  Attempt {attempt} failed: {exc}")
            if attempt == 4:
                raise
            time.sleep(3)
    return ""


def verify_remote_release(headers: dict, assets_to_upload: list[Path]) -> None:
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    assert data.get("tag_name") == TAG, f"Tag mismatch: {data.get('tag_name')}"
    assert data.get("name") == RELEASE_TITLE, f"Title mismatch: {data.get('name')}"
    assert data.get("draft") is False, "Release must not remain draft"
    wc = len((data.get("body") or "").split())
    assert 0 < wc <= 100, f"Invalid body word count: {wc}"
    remote_by_name = {a["name"]: a for a in data.get("assets", [])}
    for p in assets_to_upload:
        assert p.name in remote_by_name, f"Missing remote asset: {p.name}"
        r_size = remote_by_name[p.name]["size"]
        l_size = p.stat().st_size
        assert r_size == l_size, f"Size mismatch for {p.name}: remote={r_size} vs local={l_size}"
    print(f"Verified remote release {TAG}: title={data.get('name')!r}, words={wc}, assets={len(assets_to_upload)}/{len(assets_to_upload)} size-matched.")


def main() -> int:
    validate_release()
    token = get_github_token()
    assert token, "Could not get GitHub token from git credentials."
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Antigravity-Release-Deployer",
    }

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

    rel = get_or_create_release(headers)
    existing_assets = {a["name"]: a for a in rel.get("assets", [])}
    for p in assets_to_upload:
        upload_asset(rel, p, headers, existing_assets)

    verify_remote_release(headers, assets_to_upload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
