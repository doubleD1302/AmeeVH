#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update web landing page download links to v1.0.9 for Windows and Android."""

import os, sys, shutil, subprocess
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
    
    # Update Windows links
    text = text.replace("releases/download/v1.0.8/StellaSora-Windows_v1.0.8.exe", "releases/download/v1.0.9/StellaSora-Windows_v1.0.9.exe")
    text = text.replace("downloads/StellaSora-Windows_v1.0.8.exe", "downloads/StellaSora-Windows_v1.0.9.exe")
    text = text.replace('download="StellaSora-Windows_v1.0.8.exe"', 'download="StellaSora-Windows_v1.0.9.exe"')
    text = text.replace('title="Tải Bản Cài Windows v1.0.8"', 'title="Tải Bản Cài Windows v1.0.9"')
    text = text.replace('>v1.0.8 PC<', '>v1.0.9 PC<')

    # Update Android links
    text = text.replace("releases/download/v1.0.8/StellaSora-Android_v1.0.8.apk", "releases/download/v1.0.9/StellaSora-Android_v1.0.9.apk")
    text = text.replace("downloads/StellaSora-Android_v1.0.8.apk", "downloads/StellaSora-Android_v1.0.9.apk")
    text = text.replace('download="StellaSora-Android_v1.0.8.apk"', 'download="StellaSora-Android_v1.0.9.apk"')
    text = text.replace('title="Tải Bản Cài Android v1.0.8"', 'title="Tải Bản Cài Android v1.0.9"')
    text = text.replace('>v1.0.8 APK<', '>v1.0.9 APK<')

    fp.write_text(text, encoding="utf-8")
    print(f"✓ Updated HTML: {fp}")

def update_readme(fp: Path):
    if not fp.is_file(): return
    text = fp.read_text(encoding="utf-8")
    text = text.replace("releases/download/v1.0.8/StellaSora-Windows_v1.0.8.exe", "releases/download/v1.0.9/StellaSora-Windows_v1.0.9.exe")
    text = text.replace("StellaSora-Windows_v1.0.8.exe", "StellaSora-Windows_v1.0.9.exe")
    text = text.replace("releases/download/v1.0.8/StellaSora-Android_v1.0.8.apk", "releases/download/v1.0.9/StellaSora-Android_v1.0.9.apk")
    text = text.replace("StellaSora-Android_v1.0.8.apk", "StellaSora-Android_v1.0.9.apk")
    fp.write_text(text, encoding="utf-8")
    print(f"✓ Updated README: {fp}")

def main():
    print("=== ĐỒNG BỘ LINK TẢI TRÊN WEB SANG v1.0.9 ===")
    
    # 1. Update HTML files
    for fp in html_files:
        update_html(fp)

    # 2. Update README in work/Amee-Web
    update_readme(ROOT / "work/Amee-Web/README.md")

    # 3. Copy files to dist Web downloads and web downloads
    win_exe = ROOT / "dist/StellaSora-Windows_v1.0.9.exe"
    apk = ROOT / "dist/StellaSora-Android_v1.0.9.apk"
    
    for d_dir in [ROOT / "dist/Web_Tai_Launcher_Viet_Hoa/downloads", ROOT / "web/downloads", ROOT / "work/Amee-Web/downloads"]:
        d_dir.mkdir(parents=True, exist_ok=True)
        if win_exe.is_file():
            shutil.copy2(win_exe, d_dir / "StellaSora-Windows_v1.0.9.exe")
            shutil.copy2(win_exe, d_dir / "StellaSora_Launcher.exe")
        if apk.is_file():
            shutil.copy2(apk, d_dir / "StellaSora-Android_v1.0.9.apk")
            shutil.copy2(apk, d_dir / "StellaSora_VietHoa.apk")
        print(f"✓ Copied v1.0.9 binaries to {d_dir}")

    # 4. Commit and push Amee-Web repo
    amee_web_dir = ROOT / "work/Amee-Web"
    if (amee_web_dir / ".git").is_dir():
        print("\nCommitting and pushing to doubleD1302/Amee-Web...")
        subprocess.run(["git", "add", "-A"], cwd=amee_web_dir)
        subprocess.run(["git", "commit", "-m", "feat: sync download links to v1.0.9"], cwd=amee_web_dir)
        r = subprocess.run(["git", "push", "origin", "main"], cwd=amee_web_dir)
        if r.returncode == 0:
            print("✓ Successfully pushed Amee-Web to GitHub!")
        else:
            print("Notice: Amee-Web push exited with code", r.returncode)

if __name__ == "__main__":
    main()
