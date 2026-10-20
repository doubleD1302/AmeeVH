import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")
with open(glossary_file, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
forbidden_rules = master_glossary.get("forbidden", {})

batch_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json")
with open(batch_path, "r", encoding="utf-8") as f:
    batch_data = json.load(f)

print(f"Glossary Surveyor: Scanning {len(batch_data)} clean story dialogue lines...")

# Story & Character terms surveyed from 10k clean lines
NEW_STORY_TERMS = {
    # Absolute Mandatory Rule: Firstlight Noya -> Noya - Khải Minh
    "Firstlight Noya": "Noya - Khải Minh",
    "First Light Noya": "Noya - Khải Minh",
    "Firstlight": "Khải Minh",
    "Noya - Khải Minh": "Noya - Khải Minh",
    
    # Core Characters & Key Persons
    "Noya": "Noya",
    "Amber": "Amber",
    "Kohaku": "Kohaku",
    "Iris": "Iris",
    "Fuyuka": "Fuyuka",
    "Lady Fuyuka": "Tiểu Thư Fuyuka",
    "Lady Iris": "Tiểu Thư Iris",
    "Nazuka": "Nazuka",
    "Nazuna": "Nazuna",
    "Dorra": "Dorra",
    "Torina": "Torina",
    "Chitose": "Chitose",
    "Minova": "Minova",
    "Bastelina": "Bastelina",
    "Ayame": "Ayame",
    "Seina": "Seina",
    "Feagin": "Feagin",
    "Chief Feagin": "Trưởng Hội Feagin",
    "Serena": "Serena",
    "Vita": "Vita",
    "Galavera": "Galavera",
    "Daria": "Daria",
    "Loxy": "Loxy",
    "Allie": "Allie",
    "Aunt Allie": "Dì Allie",
    "Canace": "Canace",
    "Professor Canace": "Giáo Sư Canace",
    "Tilia": "Tilia",
    "Masked Knight Tilia": "Kỵ Sĩ Mặt Nạ Tilia",
    "Masked Knight": "Kỵ Sĩ Mặt Nạ",
    "Masked Knights": "Các Kỵ Sĩ Mặt Nạ",
    "White-Haired Girl": "Thiếu Nữ Tóc Trắng",
    "Anxious Girl": "Cô Gái Bồn Chồn",
    "Optimistic Girl": "Cô Gái Lạc Quan",
    "Admiring Driver": "Tài Xế Ngưỡng Mộ",
    "Hidden Lord": "Chúa Tể Ẩn Danh",

    # Factions, Roles, Organizations & Vehicles
    "Boss": "Sếp",
    "Tyrant": "Bạo Chúa",
    "The Tyrant": "Bạo Chúa",
    "Trekkers": "Các Lữ Khách",
    "Creta Trading": "Thương Hội Creta",
    "The Creta Trading": "Thương Hội Creta",
    "Creta Trading Lobby": "Sảnh Thương Hội Creta",
    "Creta Trading Corridor": "Hành Lang Thương Hội Creta",
    "Grace Imperium Vault": "Kim Khố Ý Chí Ân Tứ",
    "Platinum Academy": "Học Viện Bạch Kim",
    "Lucky Oasis": "Ốc Đảo May Mắn",
    "The Lucky Oasis": "Ốc Đảo May Mắn",
    "Big Three": "Tam Đại Thế Lực",
    "Imperial Guard": "Kỵ Sĩ Hoàng Gia",
    "Imperial Guards": "Kỵ Sĩ Hoàng Gia",
    "The Imperial Guard": "Kỵ Sĩ Hoàng Gia",
    "Imperial Knights": "Kỵ Sĩ Hoàng Gia",
    "Imperial Guard Knights": "Kỵ Sĩ Cận Vệ Hoàng Gia",
    "Trekkers' House": "Nhà Lữ Khách",
    "Old Trekkers' House": "Nhà Lữ Khách Xưa",
    "Ash Orphanage": "Viện Mồ Côi Ash",

    # Places & Story Lore
    "Monoliths": "Các Cự Tháp",
    "The Monolith": "Cự Tháp",
    "Thousand Monoliths": "Vạn Cự Tháp",
    "Pluvia Month": "Tháng Pluvia",
    "Floris Month": "Tháng Floris",
    "Outside Philae": "Ngoại Ô Philae",
    "Gold District": "Quận Vàng",
    "Ash District": "Quận Ash",
    "White Room": "Căn Phòng Trắng",
    "Stargate Inn": "Quán Trọ Cổng Sao",
    "Phoenix Diner": "Tiệm Ăn Phượng Hoàng",
    "Waterway Bridge Corridor": "Hành Lang Cầu Kênh Nước",
    "Cang Wu": "Thương Ngô",

    # Items, Story Quests, Concepts & Monsters
    "Stellaroid": "Tinh Hài",
    "Stellaroids": "Tinh Hài",
    "Soul Stone": "Hồn Thạch",
    "Soul Stones": "Hồn Thạch",
    "Soul Shop": "Cửa Hàng Linh Hồn",
    "Boss Accord": "Hiệp Ước Của Sếp",
    "Tyrant Accord": "Giao Kèo Bạo Chúa",
    "The Awakening Reset": "Khởi Đầu Thức Tỉnh",
    "Chronicles of New Nova": "Biên Niên Sử Tân Nova",
    "The Legend of the Twin Stars": "Truyền Thuyết Ngôi Sao Đôi",
    "Fall of the Twin Stars": "Sự Sụp Đổ Của Ngôi Sao Đôi",
    "The Lost Kitten": "Mèo Con Lạc Lối",
    "Wilderness Survival Contest": "Cuộc Thi Sinh Tồn Hoang Dã",
    "Fast and Focused": "Tốc Độ & Tập Trung",
    "Tamago Pet": "Thú Cưng Tamago",
    "Pep Pep Juice": "Nước Ép Năng Lượng Pep Pep",
    "Wish Box": "Hộp Điều Ước",
    "Wishing Box": "Hộp Nguyện Ước",
    "Scepter of Light": "Vương Trượng Ánh Sáng",
    "Prize Claw": "Máy Gắp Thú",
    "Tawny Nightingale": "Dạ Oanh Nâu",
    "Bark Boars": "Heo Rừng Vỏ Cây",
    "Lapis Eagle": "Ưng Lam Ngọc",
    "Purple Nettles": "Tầm Ma Tím",
    "Jinken Hitotsu": "\"Jinken Hitotsu\" (Nhân Kiếm Hợp Nhất)",
}

# Absolute Forbidden Rules additions (ensure "Sơ Quang" is strictly banned)
NEW_FORBIDDEN_RULES = {
    "Sơ Quang": "Khải Minh (Firstlight Noya -> Noya - Khải Minh, tuyệt đối cấm dùng Sơ Quang)",
    "Noya Sơ Quang": "Noya - Khải Minh",
    "Sơ Quang Noya": "Noya - Khải Minh",
    "Firstlight Sơ Quang": "Khải Minh",
}

added_count = 0
for term, trans in NEW_STORY_TERMS.items():
    if term not in existing_terms:
        existing_terms[term] = trans
        added_count += 1
    elif existing_terms[term] != trans and term == "Firstlight Noya":
        existing_terms[term] = trans

forbidden_added_count = 0
for fb_key, fb_val in NEW_FORBIDDEN_RULES.items():
    if fb_key not in forbidden_rules:
        forbidden_rules[fb_key] = fb_val
        forbidden_added_count += 1

master_glossary["terms"] = existing_terms
master_glossary["forbidden"] = forbidden_rules

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(master_glossary, f, indent=2, ensure_ascii=False)

survey_report_path = os.path.join(viet_dir, r"work\reviews\glossary_survey_10k_stories.json")
report_data = {
    "scanned_file": "work/batches/batch_10000_avg_clean.json",
    "scanned_dialogues_count": len(batch_data),
    "total_terms_in_glossary": len(existing_terms),
    "total_forbidden_rules": len(forbidden_rules),
    "newly_added_story_terms_count": added_count,
    "newly_added_forbidden_rules_count": forbidden_added_count,
    "absolute_rules": {
        "Firstlight Noya": "Noya - Khải Minh (Banned: Sơ Quang)",
        "tone_dialogue": "Anime đời thường trong sáng, tự nhiên, thuần Việt, không lạm dụng Hán Việt",
        "tone_entities": "Hán Việt uy nghi, đúng chuẩn cho chiêu thức, tổ chức, danh xưng chính quy"
    },
    "surveyed_new_terms": NEW_STORY_TERMS,
    "forbidden_additions": NEW_FORBIDDEN_RULES
}

with open(survey_report_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print(f"Glossary Surveyor complete:")
print(f"  - Scanned clean batch: {batch_path} ({len(batch_data)} dialogue strings)")
print(f"  - Newly added terms: {added_count}")
print(f"  - Total terms in Master Glossary: {len(existing_terms)}")
print(f"  - Total forbidden rules: {len(forbidden_rules)}")
print(f"  - Report saved to: {survey_report_path}")
