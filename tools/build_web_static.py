#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/build_web_static.py
Biên dịch toàn bộ dữ liệu từ work/sheets_export/*.csv, từ điển, hồ sơ nhân vật và tài nguyên web
thành gói web tĩnh hoàn chỉnh trong web/story_translator/ để sẵn sàng deploy 1-click lên Cloudflare Pages.
"""

import csv
import json
import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "web" / "story_translator"
DATA_DIR = APP_DIR / "data"
CHAPTERS_DATA_DIR = DATA_DIR / "chapters"
SHEETS_EXPORT_DIR = ROOT_DIR / "work" / "sheets_export"
OFFICIAL_ASSETS_DIR = ROOT_DIR / "work" / "stellasora_official_web_assets" / "assets"
CHARACTERS_SRC = ROOT_DIR / "work" / "stellasora_official_web_assets" / "characters_enriched.json"
SCENE_FRIENDLY_SRC = ROOT_DIR / "work" / "stellasora_official_web_assets" / "scene_friendly_titles.json"
WEB_ASSETS_SRC = ROOT_DIR / "web" / "assets"
TRANSLATOR_STATS_SRC = ROOT_DIR / "work" / "translator_stats.json"

CHAPTER_TITLE_MAP = {
    "Chuong_0_MainStory": ("Chương 0 - Mở Đầu", "Chương 0 - Mở Đầu"),
    "Chuong_1_MainStory": ("Chương 1 (Cốt truyện chính)", "Chương 1"),
    "Chuong_2_MainStory": ("Chương 2 (Cốt truyện chính)", "Chương 2"),
    "Chuong_3_MainStory": ("Chương 3 (Cốt truyện chính)", "Chương 3"),
    "Chuong_4_MainStory": ("Chương 4 (Cốt truyện chính)", "Chương 4"),
    "Chuong_5_MainStory": ("Chương 5 (Cốt truyện chính)", "Chương 5"),
    "Chuong_6_MainStory": ("Chương 6 (Cốt truyện chính)", "Chương 6"),
    "Chuong_7_MainStory": ("Chương 7 (Cốt truyện chính)", "Chương 7"),
    "Chuong_8_MainStory": ("Chương 8 (Cốt truyện chính)", "Chương 8"),
    "Chuong_9_MainStory": ("Chương 9 (Cốt truyện chính)", "Chương 9"),
    "Ngoai_Truyen_STsp": ("Ngoại truyện (Side Stories)", "Ngoại Truyện"),
    "Uy_Thac_Hoi_Quan_BBm": ("Nhiệm vụ ủy thác (BBm)", "Ủy Thác Hội Quán"),
    "Hen_Ho_Dating_DP": ("Hẹn hò nhân vật (Dating)", "Hẹn Hò Nhân Vật"),
    "Tin_Nhan_Dien_Thoai_PM": ("Tin nhắn điện thoại (PM)", "Tin Nhắn Điện Thoại"),
    "Cot_Truyen_Su_Kien_STev": ("Cốt truyện sự kiện (STev)", "Cốt Truyện Sự Kiện"),
    "Kich_Ban_CG_Memory": ("Kịch bản CG & Ký ức", "Kịch Bản Ký Ức (CG)"),
}

def load_friendly_scenes():
    if SCENE_FRIENDLY_SRC.exists():
        try:
            with open(SCENE_FRIENDLY_SRC, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def build_chapters_and_scenes(friendly_scenes):
    CHAPTERS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    chapters_meta = []
    total_all_lines = 0
    total_translated_lines = 0

    csv_files = sorted(SHEETS_EXPORT_DIR.glob("*.csv"))
    print(f"[*] Quét {len(csv_files)} file CSV cốt truyện...")

    for csv_file in csv_files:
        cid = csv_file.stem
        if cid not in CHAPTER_TITLE_MAP:
            continue
        display_name, sheet_name = CHAPTER_TITLE_MAP[cid]

        scenes = []
        current_scene = None
        total_lines = 0
        translated_lines = 0
        approved_lines = 0

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        for idx, r in enumerate(rows):
            if idx == 0:
                continue
            row_number = idx + 1
            if not r or not r[0]:
                continue

            if r[0].startswith("🌟") or len(r) == 1:
                scene_title = r[0].replace("🌟", "").strip()
                current_scene = {
                    "title": scene_title,
                    "scene_id": "",
                    "badge": "",
                    "lines": []
                }
                scenes.append(current_scene)
                continue

            if current_scene is None:
                current_scene = {"title": "KHỞI ĐẦU", "scene_id": "", "badge": "", "lines": []}
                scenes.append(current_scene)

            total_lines += 1
            scene_id = r[0] if len(r) > 0 else ""
            if current_scene and not current_scene.get("scene_id") and scene_id:
                current_scene["scene_id"] = scene_id
                f_info = friendly_scenes.get(scene_id)
                if f_info:
                    current_scene["title"] = f_info.get("display", current_scene["title"])
                    current_scene["badge"] = f_info.get("badge", scene_id)
                    current_scene["code"] = scene_id

            line_id = r[1] if len(r) > 1 else ""
            speaker = r[2] if len(r) > 2 else "Dẫn chuyện"
            en_text = r[3] if len(r) > 3 else ""
            old_vi = r[4] if len(r) > 4 else ""
            new_vi = r[5] if len(r) > 5 else ""
            translator = r[6] if len(r) > 6 else ""
            status = r[7] if len(r) > 7 else "Chờ dịch"
            notes = r[8] if len(r) > 8 else ""

            if new_vi and (new_vi != en_text or status == "Đã duyệt"):
                translated_lines += 1
            if status == "Đã duyệt":
                approved_lines += 1

            current_scene["lines"].append({
                "row_index": row_number,
                "scene_id": scene_id,
                "line_id": line_id,
                "speaker": speaker,
                "en": en_text,
                "old_vi": old_vi,
                "new_vi": new_vi,
                "translator": translator,
                "status": status,
                "notes": notes
            })

        pct = round((translated_lines / total_lines * 100), 1) if total_lines > 0 else 0
        total_all_lines += total_lines
        total_translated_lines += translated_lines

        chapter_info = {
            "id": cid,
            "title": display_name,
            "sheet_name": sheet_name,
            "total_lines": total_lines,
            "translated_lines": translated_lines,
            "approved_lines": approved_lines,
            "progress_pct": pct
        }
        chapters_meta.append(chapter_info)

        # Ghi file JSON chi tiết cho từng chương
        chapter_detail = {
            "chapter_id": cid,
            "title": display_name,
            "sheet_name": sheet_name,
            "scenes": scenes
        }
        chapter_json_path = CHAPTERS_DATA_DIR / f"{cid}.json"
        with open(chapter_json_path, "w", encoding="utf-8") as f:
            json.dump(chapter_detail, f, ensure_ascii=False, indent=2)

    # Ghi file chapters.json tổng quan
    chapters_json_path = DATA_DIR / "chapters.json"
    with open(chapters_json_path, "w", encoding="utf-8") as f:
        json.dump(chapters_meta, f, ensure_ascii=False, indent=2)

    print(f"✓ Đã tạo {len(chapters_meta)} file chương JSON ({total_translated_lines}/{total_all_lines} câu đã dịch).")

def build_glossary():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    glossary_terms = []
    glossary_json_src = SHEETS_EXPORT_DIR / "glossary_terms.json"
    glossary_csv_src = SHEETS_EXPORT_DIR / "01_Thong_Nhat_Danh_Tu.csv"

    if glossary_json_src.exists():
        try:
            with open(glossary_json_src, "r", encoding="utf-8") as f:
                glossary_terms = json.load(f)
        except Exception:
            pass

    if not glossary_terms and glossary_csv_src.exists():
        with open(glossary_csv_src, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            for r in rows[1:]:
                if len(r) >= 2 and r[0].strip():
                    glossary_terms.append({
                        "category": r[0].strip() if len(r) > 0 else "Chung",
                        "en": r[1].strip() if len(r) > 1 else "",
                        "vi": r[2].strip() if len(r) > 2 else "",
                        "notes": r[3].strip() if len(r) > 3 else ""
                    })

    target = DATA_DIR / "glossary.json"
    with open(target, "w", encoding="utf-8") as f:
        json.dump(glossary_terms, f, ensure_ascii=False, indent=2)
    print(f"✓ Đã tạo glossary.json ({len(glossary_terms)} thuật ngữ).")

def build_characters():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / "characters.json"
    if CHARACTERS_SRC.exists():
        shutil.copy2(CHARACTERS_SRC, target)
        print("✓ Đã copy characters.json.")

def build_leaderboard():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / "leaderboard.json"
    leaders = []
    if TRANSLATOR_STATS_SRC.exists():
        try:
            with open(TRANSLATOR_STATS_SRC, "r", encoding="utf-8") as f:
                data = json.load(f)
                leaders = sorted(list(data.values()), key=lambda x: x.get("exp", 0), reverse=True)
        except Exception:
            pass
    with open(target, "w", encoding="utf-8") as f:
        json.dump(leaders, f, ensure_ascii=False, indent=2)
    print(f"✓ Đã tạo leaderboard.json ({len(leaders)} dịch giả).")

def copy_static_assets():
    # 1. Web assets (logos, icons, themes)
    web_assets_dest = APP_DIR / "web_assets"
    web_assets_dest.mkdir(parents=True, exist_ok=True)
    if WEB_ASSETS_SRC.exists():
        for item in WEB_ASSETS_SRC.iterdir():
            if item.is_file():
                shutil.copy2(item, web_assets_dest / item.name)
        print(f"✓ Đã copy web_assets.")

    # 2. Official character assets (avatars, standees, voice lines, bgm)
    official_assets_dest = APP_DIR / "official_assets"
    official_assets_dest.mkdir(parents=True, exist_ok=True)
    
    needed_files = {"bgm-90e5d63f.mp3"}
    if CHARACTERS_SRC.exists():
        with open(CHARACTERS_SRC, "r", encoding="utf-8") as f:
            chars = json.load(f)
            for c in chars:
                if c.get("avatar"): needed_files.add(c["avatar"])
                if c.get("bigImg"): needed_files.add(c["bigImg"])
                if isinstance(c.get("audio"), list):
                    for a in c["audio"]:
                        if a.get("wav"): needed_files.add(a["wav"])

    copied_count = 0
    if OFFICIAL_ASSETS_DIR.exists():
        for fname in needed_files:
            src_fp = OFFICIAL_ASSETS_DIR / fname
            if src_fp.exists():
                shutil.copy2(src_fp, official_assets_dest / fname)
                copied_count += 1
    print(f"✓ Đã copy {copied_count}/{len(needed_files)} official_assets cần thiết.")

def main():
    print("=== BẮT ĐẦU BIÊN DỊCH GÓI WEB TĨNH CHO CLOUDFLARE PAGES ===")
    friendly_scenes = load_friendly_scenes()
    build_chapters_and_scenes(friendly_scenes)
    build_glossary()
    build_characters()
    build_leaderboard()
    copy_static_assets()
    print("=== HOÀN THÀNH: Gói web tĩnh tại web/story_translator đã sẵn sàng 100%! ===")

if __name__ == "__main__":
    main()
