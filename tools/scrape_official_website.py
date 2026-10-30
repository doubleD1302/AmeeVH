#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to discover and download all assets from https://stellasora.global/
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_URL = "https://stellasora.global/"
CDN_BASE = "https://novaweb-usstatic.yo-star.com/h5/"
OUTPUT_DIR = Path("StellaSora_VietHoa/work/stellasora_official_web_assets")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://stellasora.global/"
}

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()

def discover_assets():
    print(f"[1/4] Đang tải trang chủ {TARGET_URL}...")
    html_bytes = fetch_url(TARGET_URL)
    html_text = html_bytes.decode("utf-8", errors="ignore")

    asset_urls = set()
    js_urls = set()
    css_urls = set()

    # Find scripts and link tags in HTML
    for m in re.finditer(r'src=["\']([^"\']+)["\']', html_text):
        u = m.group(1)
        if u.endswith(".js"):
            js_urls.add(urllib.parse.urljoin(CDN_BASE, u))
        elif any(u.endswith(ext) for ext in [".png", ".jpg", ".webp", ".svg", ".ico"]):
            asset_urls.add(urllib.parse.urljoin(CDN_BASE, u))

    for m in re.finditer(r'href=["\']([^"\']+)["\']', html_text):
        u = m.group(1)
        if u.endswith(".css"):
            css_urls.add(urllib.parse.urljoin(CDN_BASE, u))
        elif any(u.endswith(ext) for ext in [".png", ".jpg", ".webp", ".svg", ".ico"]):
            asset_urls.add(urllib.parse.urljoin(CDN_BASE, u))

    print(f" -> Tìm thấy {len(js_urls)} tệp JS và {len(css_urls)} tệp CSS từ HTML.")

    # Process CSS files
    print("[2/4] Đang phân tích các tệp CSS để trích xuất font, ảnh...")
    for cu in sorted(css_urls):
        try:
            print(f"    - Đọc CSS: {cu}")
            css_bytes = fetch_url(cu)
            css_text = css_bytes.decode("utf-8", errors="ignore")
            # Save css content to memory / scan
            for url_match in re.finditer(r'url\(\s*["\']?([^"\'\)]+)["\']?\s*\)', css_text):
                raw = url_match.group(1).strip()
                if raw.startswith("data:"):
                    continue
                full_url = urllib.parse.urljoin(cu, raw)
                asset_urls.add(full_url)
        except Exception as e:
            print(f"      Lỗi đọc {cu}: {e}")

    # Process JS files
    print("[3/4] Đang phân tích các tệp JS bundles để trích xuất ảnh, video, âm thanh...")
    asset_ext_pattern = re.compile(
        r'["\']([^"\']+\.(?:png|jpg|jpeg|webp|gif|svg|mp4|webm|mp3|wav|ogg|woff|woff2|ttf|otf|json))["\']',
        re.IGNORECASE
    )
    assets_chunk_pattern = re.compile(r'["\'](assets/[a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+)["\']')

    for ju in sorted(js_urls):
        try:
            print(f"    - Đọc JS: {ju.split('/')[-1]}")
            js_bytes = fetch_url(ju)
            js_text = js_bytes.decode("utf-8", errors="ignore")

            for m in asset_ext_pattern.finditer(js_text):
                val = m.group(1).strip()
                if " " in val or "{" in val or "<" in val:
                    continue
                if val.startswith("http://") or val.startswith("https://"):
                    asset_urls.add(val)
                elif val.startswith("/"):
                    asset_urls.add(urllib.parse.urljoin(CDN_BASE, val.lstrip("/")))
                elif val.startswith("assets/"):
                    asset_urls.add(urllib.parse.urljoin(CDN_BASE, val))
                else:
                    asset_urls.add(urllib.parse.urljoin(CDN_BASE, "assets/" + val))

            for m in assets_chunk_pattern.finditer(js_text):
                val = m.group(1).strip()
                asset_urls.add(urllib.parse.urljoin(CDN_BASE, val))

        except Exception as e:
            print(f"      Lỗi đọc {ju}: {e}")

    # Also add the JS and CSS themselves
    all_targets = asset_urls | js_urls | css_urls
    print(f"\n[+] Tổng số assets phát hiện: {len(all_targets)} tệp.")
    return html_bytes, all_targets

if __name__ == "__main__":
    html_bytes, all_targets = discover_assets()
    with open("discovered_assets.json", "w", encoding="utf-8") as f:
        json.dump(sorted(list(all_targets)), f, indent=2)
    print("Đã lưu danh sách vào discovered_assets.json")
