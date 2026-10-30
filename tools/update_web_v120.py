#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync download binaries and web assets to v1.2.0 across web, dist/Web_Tai_Launcher_Viet_Hoa, and work/Amee-Web.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

html_files = [
    ROOT / "web/index.html",
    ROOT / "dist/Web_Tai_Launcher_Viet_Hoa/index.html",
    ROOT / "work/Amee-Web/index.html",
]

def update_html(fp: Path):
    if not fp.is_file():
        print(f"File not found: {fp}")
        return
    text = fp.read_text(encoding="utf-8")
    
    # Ensure v1.2.0 links are set
    for prev_ver in ("v1.0.8", "v1.0.9", "v1.1.0"):
        text = text.replace(f"releases/download/{prev_ver}/StellaSora-Windows_{prev_ver}.exe", "releases/download/v1.2.0/StellaSora-Windows_v1.2.0.exe")
        text = text.replace(f"downloads/StellaSora-Windows_{prev_ver}.exe", "downloads/StellaSora-Windows_v1.2.0.exe")
        text = text.replace(f'download="StellaSora-Windows_{prev_ver}.exe"', 'download="StellaSora-Windows_v1.2.0.exe"')
        text = text.replace(f'title="Tải Bản Cài Windows {prev_ver}"', 'title="Tải Bản Cài Windows v1.2.0"')
        text = text.replace(f'>{prev_ver} PC<', '>v1.2.0 PC<')

        text = text.replace(f"releases/download/{prev_ver}/StellaSora-Android_{prev_ver}.apk", "releases/download/v1.2.0/StellaSora-Android_v1.2.0.apk")
        text = text.replace(f"downloads/StellaSora-Android_{prev_ver}.apk", "downloads/StellaSora-Android_v1.2.0.apk")
        text = text.replace(f'download="StellaSora-Android_{prev_ver}.apk"', 'download="StellaSora-Android_v1.2.0.apk"')
        text = text.replace(f'title="Tải Bản Cài Android {prev_ver}"', 'title="Tải Bản Cài Android v1.2.0"')
        text = text.replace(f'>{prev_ver} APK<', '>v1.2.0 APK<')

    fp.write_text(text, encoding="utf-8")
    print(f"✓ Checked/Updated HTML: {fp}")

def update_readme(fp: Path):
    if not fp.is_file():
        return
    text = fp.read_text(encoding="utf-8")
    for prev_ver in ("v1.0.8", "v1.0.9", "v1.1.0"):
        text = text.replace(f"releases/download/{prev_ver}/StellaSora-Windows_{prev_ver}.exe", "releases/download/v1.2.0/StellaSora-Windows_v1.2.0.exe")
        text = text.replace(f"StellaSora-Windows_{prev_ver}.exe", "StellaSora-Windows_v1.2.0.exe")
        text = text.replace(f"releases/download/{prev_ver}/StellaSora-Android_{prev_ver}.apk", "releases/download/v1.2.0/StellaSora-Android_v1.2.0.apk")
        text = text.replace(f"StellaSora-Android_{prev_ver}.apk", "StellaSora-Android_v1.2.0.apk")
    fp.write_text(text, encoding="utf-8")
    print(f"✓ Checked/Updated README: {fp}")

def main():
    print("=== ĐỒNG BỘ WEB VÀ FILE TẢI XUỐNG SANG v1.2.0 ===")
    
    # 1. Update HTML files
    for fp in html_files:
        update_html(fp)

    # 2. Update README in work/Amee-Web
    update_readme(ROOT / "work/Amee-Web/README.md")

    # 3. Copy files to dist Web downloads, web downloads, and work/Amee-Web/downloads
    win_exe = ROOT / "dist/StellaSora-Windows_v1.2.0.exe"
    apk = ROOT / "dist/StellaSora-Android_v1.2.0.apk"
    
    assert win_exe.is_file(), f"Missing Windows executable: {win_exe}"
    assert apk.is_file(), f"Missing Android APK: {apk}"

    for d_dir in [
        ROOT / "dist/Web_Tai_Launcher_Viet_Hoa/downloads",
        ROOT / "web/downloads",
        ROOT / "work/Amee-Web/downloads",
    ]:
        d_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(win_exe, d_dir / "StellaSora-Windows_v1.2.0.exe")
        shutil.copy2(win_exe, d_dir / "StellaSora_Launcher.exe")
        shutil.copy2(apk, d_dir / "StellaSora-Android_v1.2.0.apk")
        shutil.copy2(apk, d_dir / "StellaSora_VietHoa.apk")
        print(f"✓ Copied fresh v1.2.0 binaries to {d_dir}")

    # Copy index.html and assets to work/Amee-Web
    web_src = ROOT / "web"
    amee_web = ROOT / "work/Amee-Web"
    if amee_web.is_dir():
        if (web_src / "index.html").is_file():
            shutil.copy2(web_src / "index.html", amee_web / "index.html")
        if (web_src / "assets").is_dir():
            shutil.copytree(web_src / "assets", amee_web / "assets", dirs_exist_ok=True)
        print("✓ Synced web index.html and assets to work/Amee-Web")

    # 4. Commit and push Amee-Web repo
    if (amee_web / ".git").is_dir():
        print("\nCommitting and pushing to doubleD1302/Amee-Web...")
        subprocess.run(["git", "add", "-A"], cwd=amee_web, check=True)
        # Check if there are changes
        status = subprocess.run(["git", "status", "--porcelain"], cwd=amee_web, capture_output=True, text=True).stdout.strip()
        if status:
            subprocess.run(["git", "commit", "-m", "chore: sync release v1.2.0 with publisher patch detection and vanilla restore"], cwd=amee_web, check=True)
            r = subprocess.run(["git", "push", "origin", "main"], cwd=amee_web)
            if r.returncode == 0:
                print("✓ Successfully pushed Amee-Web to GitHub!")
            else:
                print("Notice: Amee-Web push returned code", r.returncode)
        else:
            print("No changes in work/Amee-Web to commit.")

if __name__ == "__main__":
    main()
