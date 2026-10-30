# -*- coding: utf-8 -*-
"""
server/models/stats_model.py
Quản lý điểm kinh nghiệm, cấp độ và danh hiệu vinh danh dịch giả
"""

import json
import time
import threading
from backend.config import TRANSLATOR_STATS_FILE

file_lock = threading.Lock()

def update_translator_stats(translator, chapter_id, lines_count=1):
    if not translator or translator.strip() == "":
        return {"level": 1, "exp": 0, "title": "Tân Binh Lạc Lối 🌱"}

    with file_lock:
        stats = {}
        if TRANSLATOR_STATS_FILE.exists():
            try:
                stats = json.loads(TRANSLATOR_STATS_FILE.read_text(encoding="utf-8"))
            except Exception:
                stats = {}

        if translator not in stats:
            stats[translator] = {
                "name": translator,
                "translated_count": 0,
                "exp": 0,
                "level": 1,
                "title": "Tân Binh Lạc Lối 🌱",
                "chapters": {},
                "last_active": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        t_data = stats[translator]
        t_data["translated_count"] += lines_count
        t_data["exp"] += lines_count * 50
        t_data["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Level calculation
        lvl = 1 + (t_data["exp"] // 250)
        t_data["level"] = lvl

        # Title progression
        if lvl >= 50:
            t_data["title"] = "Đại Bạo Chúa Biên Dịch 👑"
        elif lvl >= 30:
            t_data["title"] = "Bậc Thầy Cổ Ngữ ✨"
        elif lvl >= 20:
            t_data["title"] = "Chuyên Viên Giải Mã 🔮"
        elif lvl >= 10:
            t_data["title"] = "Hộ Vệ Đêm Filanis ⚔️"
        elif lvl >= 5:
            t_data["title"] = "Nhà Thám Hiểm Tập Sự 🧭"
        else:
            t_data["title"] = "Tân Binh Lạc Lối 🌱"

        t_data["chapters"][chapter_id] = t_data["chapters"].get(chapter_id, 0) + lines_count

        TRANSLATOR_STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        return t_data
