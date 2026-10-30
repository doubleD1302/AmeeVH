#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full asset downloader for Stella Sora Official Website (https://stellasora.global/)
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_URL = "https://stellasora.global/"
CDN_BASE = "https://novaweb-usstatic.yo-star.com/h5/"
ROOT_DIR = Path("StellaSora_VietHoa")
OUTPUT_DIR = ROOT_DIR / "work" / "stellasora_official_web_assets"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://stellasora.global/",
    "Accept": "*/*"
}

def get_local_path(url: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/")
    # Normalize paths like h5/assets/... or assets/...
    if path.startswith("h5/"):
        path = path[3:]
    return OUTPUT_DIR / Path(path)

def download_one(url: str):
    local_path = get_local_path(url)
    if local_path.exists() and local_path.stat().st_size > 0:
        return url, "EXISTS", local_path.stat().st_size

    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = local_path.with_suffix(local_path.suffix + ".tmp")

    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                if res.status != 200:
                    return url, f"HTTP_{res.status}", 0
                data = res.read()
                with open(temp_path, "wb") as f:
                    f.write(data)
                temp_path.replace(local_path)
                return url, "OK", len(data)
        except urllib.error.HTTPError as e:
            if temp_path.exists():
                temp_path.unlink()
            return url, f"HTTP_{e.code}", 0
        except Exception as e:
            if attempt == 2:
                if temp_path.exists():
                    temp_path.unlink()
                return url, f"ERROR_{type(e).__name__}", 0
            time.sleep(1)

def run():
    print("=" * 70)
    print("STELLA SORA - FULL OFFICIAL WEB ASSET DOWNLOADER")
    print(f"Target: {TARGET_URL}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    # 1. Save index.html
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_file = OUTPUT_DIR / "index.html"
    try:
        req = urllib.request.Request(TARGET_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as res:
            html_bytes = res.read()
            with open(index_file, "wb") as f:
                f.write(html_bytes)
        print(f"[+] Đã lưu index.html ({len(html_bytes):,} bytes)")
    except Exception as e:
        print(f"[-] Lỗi tải index.html: {e}")

    # 2. Load discovered URLs
    with open("discovered_assets.json", encoding="utf-8") as f:
        urls = json.load(f)

    # Filter out external tracking scripts / APIs that aren't assets
    filtered_urls = []
    for u in urls:
        if "google" in u or "tiktok" in u or "qcloud" in u:
            continue
        filtered_urls.append(u)

    print(f"[+] Bắt đầu tải {len(filtered_urls):,} assets với đa luồng (16 threads)...")
    success_count = 0
    fail_count = 0
    total_bytes = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(download_one, url): url for url in filtered_urls}
        done = 0
        for f in as_completed(futures):
            done += 1
            url, status, size = f.result()
            if status in ("OK", "EXISTS"):
                success_count += 1
                total_bytes += size
            else:
                fail_count += 1

            if done % 50 == 0 or done == len(filtered_urls):
                elapsed = time.time() - start_time
                mb = total_bytes / (1024 * 1024)
                print(f"[{done}/{len(filtered_urls)}] Thành công: {success_count} | 404/Bỏ qua: {fail_count} | Tải: {mb:.2f} MB ({elapsed:.1f}s)")

    print("=" * 70)
    print(f"HOÀN THÀNH!")
    print(f"- Tổng số tệp thành công: {success_count:,}")
    print(f"- Tổng dung lượng: {total_bytes / (1024*1024):.2f} MB")
    print(f"- Tệp lỗi / 404: {fail_count}")
    print(f"- Lưu tại: {OUTPUT_DIR.resolve()}")
    print("=" * 70)

if __name__ == "__main__":
    run()
