#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create GitHub Release v1.0.6 and upload all 10 assets with seamless update support."""

import os, sys, json, hashlib, subprocess, time, urllib.request

REPO = "doubleD1302/AmeeVH"
TAG = "v1.0.6"
NAME = "1.0.6"
BODY = """- Hỗ trợ tự động cập nhật trực tiếp trên cả Launcher PC (Windows) và Android (Local ADB).
- Sửa lỗi khoá tệp tiến trình khi cập nhật launcher Windows.
- Tự động nhận diện bản APK mới trong ứng dụng Android và cài đặt không cần tải web.
- Hỗ trợ tương thích linh hoạt cho các phiên bản cập nhật tài nguyên mới của game.
- Đồng nhất thuật ngữ nhân vật, cốt truyện Act 1-3 và hiển thị giao diện."""

DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))

ASSETS = [
    ("StellaSora-Windows_v1.0.6.exe", "application/octet-stream"),
    ("StellaSora-Android_v1.0.6.apk", "application/vnd.android.package-archive"),
    ("android_localadb_launcher.json", "application/json"),
    ("patch_manifest.json", "application/json"),
    ("android_patch_manifest.json", "application/json"),
    ("SHA256SUMS.txt", "text/plain"),
    ("data_patched_vi.arcx", "application/octet-stream"),
    ("lua_patched_vi.arcx", "application/octet-stream"),
    ("StellaSora_AssetBundles_VI.zip", "application/zip"),
    ("StellaSora_Android_AssetBundles_VI.zip", "application/zip"),
]

def get_token():
    p = subprocess.Popen(["git", "credential", "fill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line[9:].strip()
    return ""

def get_fresh_release(headers):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    token = get_token()
    if not token:
        print("Error: Could not retrieve GitHub token from git credentials.")
        sys.exit(1)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "StellaSora-Release-Uploader",
    }

    rel = get_fresh_release(headers)
    print(f"Working on release {TAG} (id: {rel['id']})...")
    upload_url_tmpl = rel["upload_url"].split("{")[0]

    for aname, ctype in ASSETS:
        fpath = os.path.join(DIST, aname)
        if not os.path.isfile(fpath):
            print(f"Error: Asset file missing: {fpath}")
            sys.exit(1)

        size = os.path.getsize(fpath)
        rel = get_fresh_release(headers)
        existing = {a["name"]: a for a in rel.get("assets", [])}

        if aname in existing:
            cur = existing[aname]
            if cur.get("size") == size and cur.get("state") == "uploaded":
                print(f"✓ Skipping {aname} (already uploaded with exact size: {size:,} bytes)")
                continue
            else:
                aid = cur["id"]
                print(f"Deleting mismatched/partial {aname} (id: {aid})...")
                dreq = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/releases/assets/{aid}",
                    headers=headers,
                    method="DELETE",
                )
                try:
                    urllib.request.urlopen(dreq)
                    time.sleep(2)
                except Exception as e:
                    print(f"Notice deleting {aname}: {e}")

        with open(fpath, "rb") as f:
            data = f.read()

        print(f"Uploading {aname} ({size:,} bytes)...")
        up_url = f"{upload_url_tmpl}?name={aname}"
        up_req = urllib.request.Request(
            up_url,
            data=data,
            headers={
                **headers,
                "Content-Type": ctype,
                "Content-Length": str(size),
            },
            method="POST",
        )
        success = False
        for attempt in range(4):
            try:
                with urllib.request.urlopen(up_req, timeout=600) as uresp:
                    up_data = json.loads(uresp.read().decode("utf-8"))
                    print(f"✓ Uploaded {aname}: {up_data.get('browser_download_url')}")
                    success = True
                    break
            except Exception as e:
                print(f"Attempt {attempt+1} failed for {aname}: {e}")
                time.sleep(5)
                # Check if it actually uploaded
                try:
                    rel_check = get_fresh_release(headers)
                    check_map = {a["name"]: a for a in rel_check.get("assets", [])}
                    if aname in check_map and check_map[aname].get("size") == size:
                        print(f"✓ Verified {aname} was actually uploaded successfully despite network timeout!")
                        success = True
                        break
                    elif aname in check_map:
                        # delete partial asset before retrying
                        aid = check_map[aname]["id"]
                        dreq = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/assets/{aid}", headers=headers, method="DELETE")
                        urllib.request.urlopen(dreq)
                        time.sleep(2)
                except Exception:
                    pass

        if not success:
            print(f"Failed to upload {aname} after 4 attempts.")
            sys.exit(1)

    print("\n=== ALL 10 ASSETS UPLOADED AND VERIFIED FOR v1.0.6 ===")
    print(f"Release URL: {rel['html_url']}")

if __name__ == "__main__":
    main()
