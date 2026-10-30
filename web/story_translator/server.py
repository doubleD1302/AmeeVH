#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Story Translation Terminal Server (MVC Entry Point)
Backend API & Web Server connecting to Google Sheets
"""

import sys
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add current directory to sys.path so 'server' package resolves cleanly
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    PORT, APP_DIR, DATA_DIR, WEB_ASSETS_DIR, OFFICIAL_ASSETS_DIR,
    SPREADSHEET_ID, get_local_ip
)
from backend.views import serve_file
from backend.controllers import handle_get_api, handle_post_api

class StoryTranslatorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Static asset routes
        if path.startswith("/web_assets/"):
            subpath = path[len("/web_assets/"):]
            target_file = WEB_ASSETS_DIR / subpath
            if target_file.exists() and target_file.is_file():
                serve_file(self, target_file)
                return
            self.send_error(404, "Web asset not found")
            return

        if path.startswith("/official_assets/"):
            asset_subpath = path[len("/official_assets/"):]
            target_file = OFFICIAL_ASSETS_DIR / asset_subpath
            if target_file.exists() and target_file.is_file():
                serve_file(self, target_file)
                return
            self.send_error(404, "Asset not found")
            return

        if path.startswith("/data/"):
            data_subpath = path[len("/data/"):]
            target_file = DATA_DIR / data_subpath
            if target_file.exists() and target_file.is_file():
                serve_file(self, target_file)
                return
            self.send_error(404, "Data file not found")
            return

        # 2. Controller API routes
        if handle_get_api(self, path, query):
            return

        # 3. Fallback to standard static file serving (index.html, manifest.json, css/, js/, assets/)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if handle_post_api(self, path):
            return

        self.send_error(404, "Endpoint not found")

def run():
    server_address = ("0.0.0.0", PORT)
    local_ip = get_local_ip()
    print("=" * 75)
    print("🌟 STELLA SORA — TRẠM DỊCH THUẬT CỐT TRUYỆN (STORY TRANSLATION TERMINAL - MVC)")
    print("=" * 75)
    print(f"🚀 Server đang chạy tại:")
    print(f"   - Máy tính (PC / Localhost):  http://localhost:{PORT}")
    print(f"   - Điện thoại Android / Wi-Fi: http://{local_ip}:{PORT}")
    print(f"📊 Google Sheets Spreadsheet ID: {SPREADSHEET_ID}")
    print("=" * 75)

    httpd = HTTPServer(server_address, StoryTranslatorHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Đang dừng server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
