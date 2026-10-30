# -*- coding: utf-8 -*-
"""
server/controllers/api_controller.py
Xử lý các API endpoint của hệ thống trạm dịch
"""

import csv
import json
import time
import threading
from backend.config import (
    PORT, SPREADSHEET_ID, CHARACTERS_JSON, DATA_DIR, SHEETS_EXPORT_DIR,
    TRANSLATOR_STATS_FILE, CHAPTER_TITLE_MAP, get_local_ip
)
from backend.models import (
    get_friendly_scene, update_translator_stats, file_lock, get_glossary_data
)
from backend.controllers.sheets_controller import (
    sync_line_to_google_sheets, sync_glossary_from_google_sheets
)
from backend.views import send_json, serve_file

def handle_get_api(handler, path, query):
    # Characters metadata
    if path == "/api/characters":
        if CHARACTERS_JSON.exists():
            serve_file(handler, CHARACTERS_JSON, content_type="application/json; charset=utf-8")
        else:
            send_json(handler, [])
        return True

    # Server Status
    if path == "/api/status":
        send_json(handler, {
            "status": "online",
            "spreadsheet_id": SPREADSHEET_ID,
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "local_ip": get_local_ip(),
            "port": PORT
        })
        return True

    # Glossary terms
    if path == "/api/glossary":
        refresh = query.get("refresh", ["false"])[0].lower() in ["true", "1"]
        terms = get_glossary_data(refresh=refresh)
        send_json(handler, {
            "success": True,
            "total": len(terms),
            "terms": terms,
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        return True

    # List chapters & progress
    if path == "/api/chapters":
        chapters_json_file = DATA_DIR / "chapters.json"
        if chapters_json_file.exists() and not list(SHEETS_EXPORT_DIR.glob("*.csv")):
            serve_file(handler, chapters_json_file, content_type="application/json; charset=utf-8")
            return True

        chapters = []
        for csv_file in sorted(SHEETS_EXPORT_DIR.glob("*.csv")):
            cid = csv_file.stem
            if cid not in CHAPTER_TITLE_MAP:
                continue
            title_info = CHAPTER_TITLE_MAP.get(cid, (cid, cid))
            display_name, sheet_name = title_info

            total_lines = 0
            translated_lines = 0
            approved_lines = 0

            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    for r in rows[1:]:
                        if len(r) > 1 and not r[0].startswith("🌟"):
                            total_lines += 1
                            new_vi = r[5].strip() if len(r) > 5 else ""
                            status = r[7].strip() if len(r) > 7 else ""
                            en_val = r[3].strip() if len(r) > 3 else ""
                            if new_vi and (new_vi != en_val or status == "Đã duyệt"):
                                translated_lines += 1
                            if status == "Đã duyệt":
                                approved_lines += 1
            except Exception:
                pass

            pct = round((translated_lines / total_lines * 100), 1) if total_lines > 0 else 0
            chapters.append({
                "id": cid,
                "title": display_name,
                "sheet_name": sheet_name,
                "total_lines": total_lines,
                "translated_lines": translated_lines,
                "approved_lines": approved_lines,
                "progress_pct": pct
            })
        send_json(handler, chapters)
        return True

    # Chapter data
    if path == "/api/chapter_data":
        cid = query.get("id", ["Chuong_3_MainStory"])[0]
        csv_path = SHEETS_EXPORT_DIR / f"{cid}.csv"
        
        cached_json = DATA_DIR / "chapters" / f"{cid}.json"
        if not csv_path.exists() and cached_json.exists():
            serve_file(handler, cached_json, content_type="application/json; charset=utf-8")
            return True

        if not csv_path.exists():
            handler.send_error(404, "Chapter CSV not found")
            return True

        title_info = CHAPTER_TITLE_MAP.get(cid, (cid, cid))
        display_name, sheet_name = title_info

        scenes = []
        current_scene = None

        with open(csv_path, "r", encoding="utf-8") as f:
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

                scene_id = r[0] if len(r) > 0 else ""
                if current_scene and not current_scene.get("scene_id") and scene_id:
                    current_scene["scene_id"] = scene_id
                    f_info = get_friendly_scene(scene_id)
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

        send_json(handler, {
            "chapter_id": cid,
            "title": display_name,
            "sheet_name": sheet_name,
            "scenes": scenes
        })
        return True

    # Leaderboard
    if path == "/api/leaderboard":
        leaders = []
        if TRANSLATOR_STATS_FILE.exists():
            try:
                data = json.loads(TRANSLATOR_STATS_FILE.read_text(encoding="utf-8"))
                leaders = sorted(list(data.values()), key=lambda x: x.get("exp", 0), reverse=True)
            except Exception:
                pass
        send_json(handler, leaders)
        return True

    return False

def handle_post_api(handler, path):
    if path == "/api/save_line":
        length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(body)
        except Exception:
            handler.send_error(400, "Invalid JSON payload")
            return True

        chapter_id = data.get("chapter_id", "")
        sheet_name = data.get("sheet_name", "")
        row_index = int(data.get("row_index", 0))
        line_id = data.get("line_id", "")
        new_vi = data.get("new_vi", "")
        translator = data.get("translator", "").strip() or "Ẩn Danh"
        status = data.get("status", "Đã dịch")
        notes = data.get("notes", "")

        csv_path = SHEETS_EXPORT_DIR / f"{chapter_id}.csv"
        if not csv_path.exists() or row_index < 2:
            handler.send_error(404, "Invalid chapter or row index")
            return True

        with file_lock:
            with open(csv_path, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))

            if row_index - 1 < len(rows):
                row = rows[row_index - 1]
                while len(row) < 9:
                    row.append("")
                row[5] = new_vi
                row[6] = translator
                row[7] = status
                if notes:
                    row[8] = notes

                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)

        user_stats = update_translator_stats(translator, chapter_id, 1)

        if sheet_name:
            t = threading.Thread(
                target=sync_line_to_google_sheets,
                args=(sheet_name, row_index, new_vi, translator, status)
            )
            t.daemon = True
            t.start()

        send_json(handler, {
            "success": True,
            "message": f"Đã lưu câu {line_id}! Dịch giả: {translator}",
            "exp_gained": 50,
            "user_stats": user_stats
        })
        return True

    if path == "/api/sync_glossary":
        success, count, msg = sync_glossary_from_google_sheets()
        terms = get_glossary_data()
        send_json(handler, {
            "success": success,
            "total": len(terms),
            "message": msg,
            "terms": terms
        })
        return True

    return False
