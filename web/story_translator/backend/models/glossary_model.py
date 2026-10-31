# -*- coding: utf-8 -*-
"""
server/models/glossary_model.py
Quản lý nạp, phân loại và lưu trữ từ điển thuật ngữ game
"""

import csv
import json
from backend.config import GLOSSARY_CSV, GLOSSARY_JSON, GLOSSARY_CONFIG_JSON

def get_friendly_category(raw_cat):
    c = (raw_cat or "General").lower()
    if any(k in c for k in ["char", "role", "npc"]): return "Nhân Vật & Đại Từ"
    if any(k in c for k in ["combat", "skill", "talent"]): return "Chiến Đấu & Kỹ Năng"
    if any(k in c for k in ["monster", "boss"]): return "Quái Vật & Boss"
    if any(k in c for k in ["loc", "dungeon"]): return "Địa Danh & Bản Đồ"
    if any(k in c for k in ["item", "currency", "vehicle", "weapon"]): return "Vật Phẩm & Trang Bị"
    if any(k in c for k in ["ui", "progression"]): return "Giao Diện & Hệ Thống"
    if any(k in c for k in ["lore", "faction", "event", "calendar", "idiom", "race"]): return "Cốt Truyện & Thế Giới"
    return "Chung"

def load_category_lookup():
    cat_lookup = {}
    if GLOSSARY_CONFIG_JSON.exists():
        try:
            gj = json.loads(GLOSSARY_CONFIG_JSON.read_text(encoding="utf-8"))
            if isinstance(gj, dict):
                for e in gj.get("entries", []):
                    src = e.get("source", "").strip().lower()
                    if src:
                        cat_lookup[src] = e.get("category", "General")
        except Exception:
            pass
    return cat_lookup

def parse_glossary_csv(csv_path):
    if not csv_path.exists():
        return []
    cat_lookup = load_category_lookup()
    terms = []
    current_group = "General"
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                if not r:
                    continue
                t0 = r[0].strip()
                if t0.startswith("---") and t0.endswith("---"):
                    current_group = t0.replace("---", "").strip()
                    continue
                if len(r) >= 2 and r[0] != "Danh từ gốc (EN)" and not t0.startswith("BẢNG THỐNG NHẤT") and not t0.startswith("Danh từ chuẩn"):
                    en = r[0].strip()
                    vi = r[1].strip() if len(r) > 1 else ""
                    raw_cat = r[2].strip() if len(r) > 2 else ""
                    if not raw_cat or raw_cat == "General":
                        raw_cat = cat_lookup.get(en.lower(), current_group)
                    notes = r[3].strip() if len(r) > 3 else ""
                    status = r[4].strip() if len(r) > 4 else "approved"
                    if en and vi:
                        friendly_cat = get_friendly_category(raw_cat)
                        terms.append({
                            "en": en,
                            "vi": vi,
                            "category": friendly_cat,
                            "raw_category": raw_cat,
                            "notes": notes,
                            "status": status
                        })
        if terms:
            GLOSSARY_JSON.write_text(json.dumps(terms, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Glossary Parse] Lỗi: {e}")
    return terms

def get_glossary_data(refresh=False):
    from backend.controllers.sheets_controller import sync_glossary_from_google_sheets
    if refresh:
        success, count, msg = sync_glossary_from_google_sheets()
        if success and GLOSSARY_JSON.exists():
            try:
                data = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
                return data.get("terms", data) if isinstance(data, dict) else data
            except Exception:
                pass

    if GLOSSARY_JSON.exists():
        try:
            data = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
            return data.get("terms", data) if isinstance(data, dict) else data
        except Exception:
            pass

    if GLOSSARY_CSV.exists():
        return parse_glossary_csv(GLOSSARY_CSV)

    return []
