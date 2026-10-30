#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Đổi nhân vật người chơi / nhân vật chính từ 'Sylar' về lại 'Main'.
Áp dụng trên:
- Các file JSON kịch bản chương trong web/story_translator/data/chapters/
- Bản sao trong work/SS-Trans/data/chapters/
- Tiêu đề bối cảnh scene_friendly_titles.json
- Dữ liệu google_sheets_batch_data.json
"""

import os
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    total_speaker_replaced = 0
    chapters_dirs = [
        ROOT / "web" / "story_translator" / "data" / "chapters",
        ROOT / "work" / "SS-Trans" / "data" / "chapters"
    ]

    for cdir in chapters_dirs:
        if not cdir.exists():
            continue
        for fpath in cdir.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                modified = False
                for scene in data.get("scenes", []):
                    for line in scene.get("lines", []):
                        if line.get("speaker") == "Sylar":
                            line["speaker"] = "Main"
                            total_speaker_replaced += 1
                            modified = True
                if modified:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"[OK] Cập nhật: {fpath.name}")
            except Exception as e:
                print(f"[ERR] Lỗi xử lý {fpath.name}: {e}")

    print(f"-> Đã chuyển đổi tổng cộng {total_speaker_replaced} lượt speaker từ 'Sylar' -> 'Main'.")

    # 2. scene_friendly_titles.json
    titles_file = ROOT / "work" / "stellasora_official_web_assets" / "scene_friendly_titles.json"
    if titles_file.exists():
        with open(titles_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "Sylar" in content:
            new_content = content.replace("Sylar", "Main")
            with open(titles_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("[OK] Cập nhật: scene_friendly_titles.json ('Sylar' -> 'Main')")

    # 3. google_sheets_batch_data.json
    gs_file = ROOT / "work" / "batches" / "google_sheets_batch_data.json"
    if gs_file.exists():
        with open(gs_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "Sylar" in content:
            new_content = content.replace('"Sylar"', '"Main"').replace('Sylar', 'Main')
            with open(gs_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("[OK] Cập nhật: google_sheets_batch_data.json ('Sylar' -> 'Main')")

if __name__ == "__main__":
    main()
