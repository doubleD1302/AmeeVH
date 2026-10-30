# -*- coding: utf-8 -*-
"""
server/controllers/sheets_controller.py
Xử lý đồng bộ dữ liệu thời gian thực giữa server và Google Sheets qua gsheets CLI
"""

import subprocess
from backend.config import SPREADSHEET_ID, GLOSSARY_CSV, SHEETS_EXPORT_DIR, escape_sheets_cell

def sync_line_to_google_sheets(sheet_name, row_index, new_vi, translator, status):
    """Executes gsheets CLI in background to write F{row}:H{row}"""
    try:
        val_f = escape_sheets_cell(new_vi)
        val_g = escape_sheets_cell(translator)
        val_h = escape_sheets_cell(status)
        values_str = f"{val_f},{val_g},{val_h}"
        range_str = f"'{sheet_name}'!F{row_index}:H{row_index}"
        cmd = f"gsheets mutate write {SPREADSHEET_ID} \"{range_str}\" \"{values_str}\""
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            print(f"[Sheets Sync] Thành công: {range_str} -> Dịch giả: {translator}")
        else:
            print(f"[Sheets Sync] Lỗi {res.returncode}: {res.stderr}")
    except Exception as e:
        print(f"[Sheets Sync] Ngoại lệ: {e}")

def sync_glossary_from_google_sheets():
    """Fetches sheet '01. Thống Nhất Danh Từ' from Google Sheets via gsheets CLI"""
    from backend.models.glossary_model import parse_glossary_csv
    try:
        SHEETS_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        cmd = f'gsheets readonly export {SPREADSHEET_ID} "{GLOSSARY_CSV}" --sheet "01. Thống Nhất Danh Từ" --format csv'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            cmd_legacy = f'gsheets export {SPREADSHEET_ID} "{GLOSSARY_CSV}" --sheet "01. Thống Nhất Danh Từ" --format csv'
            res = subprocess.run(cmd_legacy, shell=True, capture_output=True, text=True, encoding="utf-8")

        if res.returncode == 0 and GLOSSARY_CSV.exists():
            terms = parse_glossary_csv(GLOSSARY_CSV)
            print(f"[Glossary Sync] Đã đồng bộ {len(terms)} thuật ngữ từ Google Sheets!")
            return True, len(terms), f"Đã đồng bộ {len(terms)} thuật ngữ từ Google Sheets!"
        else:
            err = res.stderr or res.stdout
            print(f"[Glossary Sync] Thất bại: {err}")
            return False, 0, f"Lỗi export Google Sheets: {err}"
    except Exception as e:
        print(f"[Glossary Sync] Ngoại lệ: {e}")
        return False, 0, str(e)
