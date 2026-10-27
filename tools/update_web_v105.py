#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

files = [
    Path("web/index.html"),
    Path("dist/Web_Tai_Launcher_Viet_Hoa/index.html"),
    Path("work/Amee-Web/index.html")
]

for fp in files:
    if not fp.exists():
        print(f"File not found: {fp}")
        continue
    content = fp.read_text(encoding="utf-8")
    new_content = (
        content
        .replace("releases/download/v1.0.4/StellaSora-Windows_v1.0.4.exe", "releases/download/v1.0.5/StellaSora-Windows_v1.0.5.exe")
        .replace("downloads/StellaSora-Windows_v1.0.4.exe", "downloads/StellaSora-Windows_v1.0.5.exe")
        .replace('download="StellaSora-Windows_v1.0.4.exe"', 'download="StellaSora-Windows_v1.0.5.exe"')
        .replace('title="Tải Bản Cài Windows v1.0.4"', 'title="Tải Bản Cài Windows v1.0.5"')
        .replace('>v1.0.4 PC<', '>v1.0.5 PC<')
    )
    if content != new_content:
        fp.write_text(new_content, encoding="utf-8")
        print(f"Updated {fp}")
    else:
        print(f"No changes made to {fp}")
