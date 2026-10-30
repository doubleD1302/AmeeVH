# -*- coding: utf-8 -*-
"""
server/config.py
Configuration, paths and helper constants for Stella Sora Story Translator Server
"""

import socket
from pathlib import Path

PORT = 8088
APP_DIR = Path(__file__).resolve().parent.parent

# Path detection (SS-Trans repo vs StellaSora_VietHoa workspace)
if (APP_DIR / "data").exists():
    DATA_DIR = APP_DIR / "data"
    WEB_ASSETS_DIR = APP_DIR / "web_assets"
    OFFICIAL_ASSETS_DIR = APP_DIR / "official_assets"
    CHARACTERS_JSON = DATA_DIR / "characters_enriched.json" if (DATA_DIR / "characters_enriched.json").exists() else DATA_DIR / "characters.json"
    SCENE_FRIENDLY_JSON = DATA_DIR / "scene_friendly_titles.json"
    SHEETS_EXPORT_DIR = DATA_DIR / "sheets_export" if (DATA_DIR / "sheets_export").exists() else DATA_DIR
    TRANSLATOR_STATS_FILE = DATA_DIR / "translator_stats.json"
    GLOSSARY_CSV = SHEETS_EXPORT_DIR / "01_Thong_Nhat_Danh_Tu.csv"
    GLOSSARY_JSON = DATA_DIR / "glossary.json" if (DATA_DIR / "glossary.json").exists() else SHEETS_EXPORT_DIR / "glossary_terms.json"
    GLOSSARY_CONFIG_JSON = DATA_DIR / "glossary.json"
else:
    ROOT_DIR = APP_DIR.parent.parent
    DATA_DIR = APP_DIR
    WEB_ASSETS_DIR = ROOT_DIR / "web" / "assets"
    OFFICIAL_ASSETS_DIR = ROOT_DIR / "work" / "stellasora_official_web_assets" / "assets"
    CHARACTERS_JSON = ROOT_DIR / "work" / "stellasora_official_web_assets" / "characters_enriched.json"
    SCENE_FRIENDLY_JSON = ROOT_DIR / "work" / "stellasora_official_web_assets" / "scene_friendly_titles.json"
    SHEETS_EXPORT_DIR = ROOT_DIR / "work" / "sheets_export"
    TRANSLATOR_STATS_FILE = ROOT_DIR / "work" / "translator_stats.json"
    GLOSSARY_CSV = SHEETS_EXPORT_DIR / "01_Thong_Nhat_Danh_Tu.csv"
    GLOSSARY_JSON = SHEETS_EXPORT_DIR / "glossary_terms.json"
    GLOSSARY_CONFIG_JSON = ROOT_DIR / "config" / "glossary.json"

SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"

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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def escape_sheets_cell(val):
    if not val:
        return " "
    val = str(val).replace("\r", "").replace("\n", " ")
    val = val.replace(",", "\\,").replace("\"", "\\\"")
    return val
