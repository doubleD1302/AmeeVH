import json
import os
import re

batches_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches"
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

# Load EN-CN table maps
en_tables = {}
cn_tables = {}
for fname in os.listdir(entries_dir):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(entries_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and len(d) > 0:
            first_k = list(d.keys())[0]
            tbl_name = first_k.split(".")[0]
            first_v = str(list(d.values())[0])
            has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in first_v)
            if has_cn:
                cn_tables[tbl_name] = fpath
            else:
                en_tables[tbl_name] = fpath
    except Exception:
        pass

print(f"Loaded {len(en_tables)} EN tables and {len(cn_tables)} CN tables.")

def get_cn_table(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Load current master glossary
master_glossary_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\config\master_glossary.json"
with open(master_glossary_path, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

current_terms = master_glossary.get("terms", {})
current_terms_lower = {k.lower(): (k, v) for k, v in current_terms.items()}

print(f"Current master glossary terms count: {len(current_terms)}")

# Let's inspect target tables per pillar
pillar_targets = {
    "pillar1": {
        "file": "pillar1_dungeons_monsters.json",
        "tables": {
            "MonsterManual": {"name_field": "1", "desc_field": "2", "cat": "Quái vật & Boss"},
            "RegionBoss": {"name_field": "1", "cat": "Boss Thế Giới / Khu Vực"},
            "TravelerDuelBoss": {"name_field": "1", "cat": "Đấu Trường Lữ Khách"},
            "TowerDefenseMonster": {"name_field": "1", "cat": "Quái vật Thủ Thành"},
            "InfinityTower": {"name_field": "1", "cat": "Tháp Vô Tận & Tầng"},
            "InfinityTowerDifficulty": {"name_field": "1", "cat": "Độ Khó Tháp Vô Tận"},
            "StarTowerGroup": {"name_field": "1", "cat": "Tháp Sao & Bí Cảnh"},
            "TravelerDuelChallengeAffix": {"name_field": "1", "cat": "Từ Tố & Chiêu Thức Boss"},
            "RegionBossAffix": {"name_field": "1", "cat": "Kỹ Năng Boss Thế Giới"},
            "SoldierPotential": {"name_field": "1", "cat": "Thiên Phú Quân Cờ"},
            "TowerDefensePotential": {"name_field": "1", "cat": "Tiềm Năng Thủ Thành"}
        }
    },
    "pillar2": {
        "file": "pillar2_voices_characters.json",
        "tables": {
            "CharacterArchiveBaseInfo": {"fields": ["1", "2"], "cat": "Hồ Sơ & Danh Xưng"},
            "CharacterDes": {"fields": ["2", "4", "5", "6", "7"], "cat": "Danh Xưng & Lối Chơi"},
            "CharacterSkin": {"name_field": "1", "desc_field": "2", "cat": "Trang Phục Nhân Vật"},
            "CharacterTag": {"name_field": "1", "cat": "Đặc Tính & Vai Trò"},
            "CharacterArchiveVoice": {"name_field": "1", "cat": "Phân Loại Giọng Thoại"}
        }
    },
    "pillar3": {
        "file": "pillar3_story_dating_quests.json",
        "tables": {
            "Plot": {"name_field": "1", "cat": "Cốt Truyện Phụ"},
            "StoryChapter": {"name_field": "2", "cat": "Chương Cốt Truyện"},
            "StorySetChapter": {"name_field": "2", "cat": "Hồi Ức & Sự Kiện Cốt Truyện"},
            "DatingLandmark": {"name_field": "1", "cat": "Địa Điểm Hẹn Hò"},
            "NPCConfig": {"name_field": "1", "cat": "Nhân Vật NPC"},
            "NPCAffinityPlot": {"name_field": "2", "cat": "Cốt Truyện Hảo Cảm NPC"}
        }
    },
    "pillar4": {
        "file": "pillar4_system_gacha_shops.json",
        "tables": {
            "Force": {"name_field": "1", "cat": "Thế Lực & Tổ Chức"},
            "ContentWord": {"name_field": "1", "cat": "Thế Lực & Lịch Sử"},
            "Honor": {"name_field": "1", "cat": "Danh Hiệu & Huy Hiệu"},
            "Title": {"name_field": "1", "cat": "Danh Xưng Người Chơi"},
            "Gacha": {"name_field": "1", "cat": "Kỳ Chiêu Mộ Gacha"},
            "GachaType": {"name_field": "1", "cat": "Loại Banner Gacha"},
            "DiscIP": {"name_field": "3", "cat": "Đĩa Nhạc & Khúc Ca"},
            "MallShop": {"name_field": "1", "cat": "Vật Phẩm Cửa Hàng"},
            "MallRecommendGroup": {"name_field": "1", "cat": "Phân Loại Cửa Hàng"},
            "AgentTab": {"name_field": "1", "cat": "Hệ Thống Ủy Thác"},
            "DictionaryTab": {"name_field": "1", "cat": "Từ Điển Bách Khoa"},
            "DictionaryEntry": {"name_field": "1", "cat": "Mục Bách Khoa"},
            "DictionaryTopBarEntry": {"name_field": "1", "cat": "Mục Thanh Điều Hướng"}
        }
    }
}

print("Survey setup completed.")
