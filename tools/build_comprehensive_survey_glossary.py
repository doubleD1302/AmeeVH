import json
import os
import re

# Base paths
ROOT_DIR = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
MASTER_GLOSSARY_PATH = os.path.join(ROOT_DIR, "config", "master_glossary.json")
REPORT_PATH = os.path.join(ROOT_DIR, "reports", "glossary_survey_report.json")
BATCHES_DIR = os.path.join(ROOT_DIR, "work", "batches")
ENTRIES_DIR = os.path.join(ROOT_DIR, "work", "research", "data_decrypted", "entries")
SKILL_TRANSLATED_PATH = os.path.join(BATCHES_DIR, "skill_names_translated.json")

# Load existing master glossary
with open(MASTER_GLOSSARY_PATH, "r", encoding="utf-8") as f:
    master_data = json.load(f)

existing_terms = master_data.get("terms", {})
existing_forbidden = master_data.get("forbidden", {})
print(f"Starting with {len(existing_terms)} existing terms and {len(existing_forbidden)} forbidden rules.")

# Load CN tables mapping
cn_tables = {}
for fname in os.listdir(ENTRIES_DIR):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(ENTRIES_DIR, fname)
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
    except Exception:
        pass

def get_cn_dict(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Load 4 pillar files
with open(os.path.join(BATCHES_DIR, "pillar1_dungeons_monsters.json"), "r", encoding="utf-8") as f: p1 = json.load(f)
with open(os.path.join(BATCHES_DIR, "pillar2_voices_characters.json"), "r", encoding="utf-8") as f: p2 = json.load(f)
with open(os.path.join(BATCHES_DIR, "pillar3_story_dating_quests.json"), "r", encoding="utf-8") as f: p3 = json.load(f)
with open(os.path.join(BATCHES_DIR, "pillar4_system_gacha_shops.json"), "r", encoding="utf-8") as f: p4 = json.load(f)

# Load pre-translated skills
with open(SKILL_TRANSLATED_PATH, "r", encoding="utf-8") as f:
    skills_translated = json.load(f)

new_terms_dict = {}
survey_categories = {}

def register_term(en_term, vi_term, category, pillar_source, notes=""):
    en_term = en_term.strip()
    vi_term = vi_term.strip()
    if not en_term or not vi_term:
        return
    # check if already in existing terms
    is_new = en_term not in existing_terms
    if is_new:
        new_terms_dict[en_term] = vi_term
    
    cat_bucket = survey_categories.setdefault(category, {
        "pillar": pillar_source,
        "count": 0,
        "new_count": 0,
        "terms": []
    })
    cat_bucket["count"] += 1
    if is_new:
        cat_bucket["new_count"] += 1
    cat_bucket["terms"].append({
        "en": en_term,
        "vi": vi_term,
        "is_new": is_new,
        "notes": notes
    })

print("Cataloging and standardizing terms across all 4 pillars...")

# =========================================================================
# 1. PRE-TRANSLATED SKILLS (Pillar 1 & Combat)
# =========================================================================
for s_en, s_vi in skills_translated.items():
    register_term(s_en, s_vi, "Kỹ Năng & Chiêu Thức Nhân Vật", "Pillar 1 / Combat", "Kỹ năng chiến đấu nhân vật chuẩn Hán Việt")

# =========================================================================
# 2. MONSTERS & BOSSES (Pillar 1)
# =========================================================================
# Element suffixes
elem_suffix_map = {
    "Rock": "Trọng Nham",
    "Torrent": "Đoan Lưu",
    "Heat": "Chước Nhiệt",
    "Gust": "Hô Khiếu",
    "Radiance": "Diệu Quang",
    "Shadow": "Ám Ảnh"
}

# Base monsters standardization map
base_monsters_map = {
    "Shrubshrews Warrior": "Chiến Binh Chuột Bụi",
    "Shrubshrew Warrior": "Chiến Binh Chuột Bụi",
    "Rabid Shrubshrew Warrior": "Chiến Binh Chuột Bụi Cuồng Bạo",
    "Shrubshrews Slinger": "Xạ Thủ Chuột Bụi",
    "Shrubshrew Slinger": "Xạ Thủ Chuột Bụi",
    "Rabid Shrubshrew Slinger": "Xạ Thủ Chuột Bụi Cuồng Bạo",
    "Citadel Shrubshrew": "Pháo Đài Chuột Bụi",
    "Tusk Minion": "Tùy Tùng Nanh Nhọn",
    "Tusk Stomper": "Mãnh Thú Nanh Nhọn",
    "Spirit of Brutality": "Linh Thú Cuồng Bạo",
    "Howling Owl": "Phệ Khiếu Kiêu",
    "Gale Owl": "Cuồng Phong Thanh Kiêu",
    "Fierce Long-Tailed Scorpion": "Bọ Cạp Đuôi Dài Hung Bạo",
    "Desert Scorpion: Eye of the Desert": "Sa Hạt: Hoang Mạc Chi Nhãn",
    "Garden of Parasite": "Khu Vườn Ký Sinh",
    "Enforcer of Silence": "Cấm Vệ Tĩnh Lặng",
    "Guardian of Thorns": "Cấm Vệ Gai Góc",
    "Oppressor of Torrents": "Cấm Vệ Cuồng Triều",
    "Suppressor of Lava": "Cấm Vệ Dung Nham",
    "Subjugator of Firmament": "Cấm Vệ Thương Khung",
    "Protector of Radiance": "Cấm Vệ Ánh Sáng",
    "Golem of Nightmares": "Cấm Vệ Ác Mộng",
    "Armadillo Fish": "Cá Tê Tê",
    "Steam Pot Hammer": "Thiết Chùy Nồi Hơi",
    "Trial Co-op Unit Model Ⅱ": "Cơ Thể Hiệp Lực Thử Nghiệm Mẫu II",
    "Trial Support Unit Model V": "Cơ Thể Viện Trợ Thử Nghiệm Mẫu V",
    "Professional UH Employee": "Nhân Viên Nông Nghiệp Chuyên Nghiệp",
    "Retriever K9": "Tuần Hồi Khuyển K9",
    "Logging Crab C8": "Phạt Mộc Giải C8",
    "Furious Stomper Crab": "Cua Chân Nặng Cáu Kỉnh",
    "Sturdy Batter": "Cầu Thủ Vạm Vỡ",
    "Clever Technician": "Kỹ Sư Linh Xảo",
    "Vollara": "Mãn Nguyệt",
    "Neuvira": "Tân Nguyệt",
    "Gauntlet of Rage": "Thịnh Nộ Quyền Khải",
    "Gauntlet of Fury": "Cuồng Nộ Quyền Khải",
    "Gauntlet of Mountain Soul": "Sơn Hồn Quyền Khải",
    "Gauntlet of Raging Waves": "Nộ Đào Quyền Khải",
    "Gauntlet of Raging Flame": "Liệt Diễm Quyền Khải",
    "Gauntlet of Swift Wind": "Phong Trì Quyền Khải",
    "Gauntlet of Luminous": "Huy Hoàng Quyền Khải",
    "Gauntlet of Spectral Shadow": "U Ảnh Quyền Khải",
    "Laid-Back Swordswoman": "Nữ Kiếm Sĩ Thư Thái",
    "Prosperity Gang Swordsman": "Kiếm Sĩ Đoàn Cung Hỷ Phát Tài",
    "Brooding Sorceress": "Thuật Sĩ U Ám",
    "Prosperity Gang Mage": "Pháp Sư Đoàn Cung Hỷ Phát Tài",
    "Heavy Armor Warrior": "Chiến Binh Trọng Giáp Vạm Vỡ",
    "Tired Newbie Employee": "Tân Binh Kiệt Sức",
    "Seasoned Elite Employee": "Tinh Anh Lão Luyện",
    "Megahand Enforcer": "Cự Thủ Hãn Tướng",
    "Nightmare Executioner": "Đao Phủ Ác Mộng",
    "Nightmare Head Executioner": "Đao Phủ Trưởng Ác Mộng",
    "Furnace Executioner": "Đao Phủ Lò Luyện",
    "Plundering Dual Blades": "Song Đao Cướp Đoạt",
    "Projectile Striker": "Xạ Thủ Pháo Đạn",
    "Space Walker": "Lữ Hành Không Gian",
    "Mountainous Space Walker": "Lữ Hành Không Gian: Trùng Loan",
    "Wandering Space Walker": "Lữ Hành Không Gian: Tuần Du",
    "Blazing Space Walker": "Lữ Hành Không Gian: Lưu Hỏa",
    "Rapid Space Walker": "Lữ Hành Không Gian: Tấn Tật",
    "Luminous Space Walker": "Lữ Hành Không Gian: Minh Huy",
    "Shadowy Space Walker": "Lữ Hành Không Gian: Quỷ Ảnh",
    "Whimagus": "Pháp Sư Whimagus",
    "Whirling Crawler": "Vuốt Sắc Xoay Tròn",
    "Whirling Thunder Claw": "Phi Toàn Phách Lịch Trảo",
    "Whirling Great Glopo": "Khối Bùn Xoáy Khổng Lồ",
    "Wrath Juggernaut": "Cự Nhân Oán Hận",
    "Wrath Rock Juggernaut": "Cừu Ách Nham Nhai Lực Sĩ",
    "Wrath Waterfall Juggernaut": "Cừu Ách Cự Thác Lực Sĩ",
    "Wrath Blaze Juggernaut": "Cừu Ách Viêm Hạc Lực Sĩ",
    "Wrath Whirlwind Juggernaut": "Cừu Ách Long Quyển Lực Sĩ",
    "Wrath Thunder Juggernaut": "Cừu Ách Lôi Dũng Lực Sĩ",
    "Wrath Chaos Juggernaut": "Cừu Ách Hỗn Độn Lực Sĩ",
    "Glopo": "Thể Băng Glopo",
    "Fat Glopo": "Glopo Béo Múp",
    "Duke Glopo Ⅲ": "Công Tước Glopo Đệ Tam",
    "King Glopo Ⅲ": "Vua Glopo Đệ Tam",
    "Cursipot": "Hũ Ma Quái Cursipot",
    "Gloomfiend": "Ảnh Ma",
    "Lucky Rubbi": "Thỏ May Mắn Rubbi",
    "Armored Coffin Sentinel": "Nhung Vệ Quan Tài",
    "Magishark": "Cá Mập Ma Đạo",
    "Jumping Sharky": "Cá Mập Nhảy Nhót",
    "Sword-and-Shield Vanguard": "Tiên Phong Kiếm Khiên",
    "Grumblegeist": "Duluo Sôi Sục",
    "Spear-Wielding Attendant": "Phong Thương Cận Thị",
    "Fiery Gaze Swordsman": "Bạch Sí Kiếm Sĩ",
    "Bouncing Fairy Light": "Đèn Màu Nảy Nhót",
    "Springseek Lantern": "Đèn Lồng Nghênh Xuân",
    "Master Digger": "Bậc Thầy Đào Bới",
    "Assistant Sweeper": "Trợ Thủ Quét Dọn",
    "Fanged Hunter": "Thợ Săn Nanh Nhọn",
    "Flashstrike Hunter": "Thợ Săn Lôi Quang",
    "Fortune": "Chiêu Tài",
    "Lucky": "Lai Phúc",
    "Gleeful Jar Spirit": "Hồ Linh Cười Vui",
    "Bursting Incense": "Bạo Liệt Hương Phân",
    "Tradewind Incense": "Tín Phong Hương Phân",
    "Fluffy Knight": "Kỵ Sĩ Lông Xù",
    "Fluffy Knight of Order": "Kỵ Sĩ Giới Luật Lông Xù",
    "Delicious Dragon": "Mạch Hương Khải Long",
    "Abyssal Sea Sovereign": "Uyên Hải Chúa Tể",
    "Abyss Silencer": "Chiêm Vọng Vực Sâu",
    "Rotting Silencer": "Chiêm Vọng Hủ Bại",
    "Flavor Dread": "Vị Giác Kinh Sợ",
    "Crispy Hooves": "Móng Giòn",
    "Crispy Hooves Deluxe": "Móng Giòn Không Ngừng",
    "Grumpy Caltrop": "Tật Lê Bực Bội",
    "Lady Dust": "Phu Nhân Bụi Tro",
    "Forbidden Beauty": "Dung Mạo Cấm Đoán",
    "Sherlock the Sleepy": "Khò Khò Sherlock",
    "Celsia: Chariot of Frenzy": "Celsia: Cuồng Bạo Chiến Xa",
    "Celsia: Chariot of Despair": "Celsia: Tuyệt Vọng Chiến Xa",
    "Exalted Puppets: Coppelius & Olympia": "Khôi Lỗi Cao Quý: Coppelius & Olympia",
    "Refrigerator Hermit Draklisk": "Thằn Lằn Ẩn Sĩ Băng",
    "Spellbound Golem": "Cự Tượng Ma Thị",
    "Lithe Beauty": "Mỹ Nhân Lưu Phong",
    "Blade of Jade": "Thúy Hoàng Chi Nhận",
    "Gobble Hexhorn Whale": "Cá Voi Lục Sừng Gobble",
    "Opera Ghost: Rovina": "Bóng Ma Nhà Hát: Rovina",
    "Count of the Duloos": "Nam Tước Duloo",
    "Grotesque Dancer": "Vũ Công Quái Dị",
    "Evernight Emberflies": "Đom Đóm Đêm Trường",
    "Tainted Mandrake": "Mandrake Nhiễm Độc",
    "Cat-stle Siege": "Đại Chiến Miêu Thành",
    "Maid For You": "Nữ Hầu Lạnh Lùng",
    "War in the Backpack": "Đại Chiến Balo"
}

# Scan MonsterManual from P1
mm_en = p1.get("MonsterManual", {}).get("entries", {})
for k, v in mm_en.items():
    if not k.endswith(".1"):
        continue
    # Check if exact match
    if v in base_monsters_map:
        register_term(v, base_monsters_map[v], "Quái Vật & Boss", "Pillar 1")
    elif ":" in v:
        # Check prefix: Suffix
        prefix, suffix = [x.strip() for x in v.split(":", 1)]
        if prefix in base_monsters_map and suffix in elem_suffix_map:
            trans = f"{base_monsters_map[prefix]}: {elem_suffix_map[suffix]}"
            register_term(v, trans, "Quái Vật & Boss", "Pillar 1")
        elif prefix in base_monsters_map:
            register_term(v, f"{base_monsters_map[prefix]}: {suffix}", "Quái Vật & Boss", "Pillar 1")
        else:
            # Fallback
            pass
    elif v.endswith("Proving Grounds"):
        base_name = v.replace(": Proving Grounds", "").strip()
        if base_name in base_monsters_map:
            register_term(v, f"{base_monsters_map[base_name]}: Đấu Trường Thử Lửa", "Quái Vật & Boss", "Pillar 1")

# Also register base monsters that weren't caught
for k, v in base_monsters_map.items():
    register_term(k, v, "Quái Vật & Boss", "Pillar 1")

# RegionBoss Proving Grounds
for k, v in p1.get("RegionBoss", {}).get("entries", {}) .items():
    if k.endswith(".1") and ": Proving Grounds" in v:
        base_name = v.replace(": Proving Grounds", "").strip()
        if base_name in base_monsters_map:
            register_term(v, f"{base_monsters_map[base_name]}: Đấu Trường Thử Lửa", "Boss Khu Vực", "Pillar 1")

# =========================================================================
# 3. KỸ NĂNG & TỪ TỐ BOSS (Pillar 1 & Pillar 4)
# =========================================================================
boss_affixes_map = {
    # RegionBossAffix
    "Lightbulb Deploy": "Triệu Hồi Bóng Đèn",
    "Hooking Crawler": "Phóng Vuốt Sắc",
    "Laser Charge": "Tích Năng Laser",
    "Spinning Windmill": "Cối Xay Gió Xoay Tròn",
    "Ground Lightning": "Sấm Sét Mặt Đất",
    "Stretch and Slam": "Vươn Dài Đập Đất",
    "Stretch and Sweep": "Vươn Dài Quét Ngang",
    "Rapid Leapstrike": "Nhảy Kích Liên Hoàn",
    "Rolling Charge": "Lăn Tròn Xung Kích",
    "Rolling Chase": "Lăn Tròn Truy Đuổi",
    "Basic Rhythm": "Nhịp Điệu Cơ Bản",
    "Crescendo Rhythm": "Tiết Tấu Dồn Dập",
    "Teleport": "Dịch Chuyển Tức Thời",
    "Repeated Performance": "Diễn Tấu Lặp Lại",
    "Slide": "Lướt Âm",
    # TravelerDuelChallengeAffix
    "Sunflower Ties": "Khuy Khế Ước",
    "Shrouded Moon: Meteor": "Ẩn Nguyệt: Lưu Tinh",
    "Shrouded Moon: Gale": "Ẩn Nguyệt: Tật Phong",
    "Entwined Gale": "Lam Phấn Triền",
    "Shadow Dance: Leaf Storm": "Ảnh Vũ: Diệp Cuồng Lam",
    "Shadow Dance: Dream Wanderer": "Ảnh Vũ: Hoa Kính Mộng",
    "Beam Sniper": "Xạ Kích Chùm Sáng",
    "All Out": "Hỏa Lực Toàn Khai",
    "Secondary Beam": "Chùm Sáng Cấp Hai",
    "Full-auto Fire": "Bắn Toàn Tự Động",
    "Semi-auto Fire": "Bắn Bán Tự Động",
    "Barrage Amplification": "Khuếch Đại Đạn Mạc",
    "Eye of the Demon Lord": "Ma Thần Chi Nhãn",
    "Blood Thirst": "Khát Máu",
    "Life Drain": "Hút Sinh Mệnh",
    "Victorious Pursuit": "Thừa Thắng Xông Lên",
    # SoldierPotential
    "Shatter Pitch": "Phá Giáp Đầu Trịch",
    "Fearless Stand": "Bất Úy Cự Tượng",
    "Wildwood Wrath": "Sâm Lâm Chi Phẫn",
    "Wildwood Outrage": "Sâm Lâm Cuồng Nộ",
    "Fearsome Dash": "Uy Hách Xung Tràng",
    "Endless Ram": "Trì Tục Xung Tràng",
    "Wildwood Watcher": "Sâm Lâm Vệ Sĩ",
    "Wildwood Patron": "Sâm Lâm Thủ Hộ Thần",
    "Wildwood Boon": "Sâm Lâm Chi Chúc",
    "Wildwood Prayer": "Sâm Lâm Chi Kỳ",
    "Power Purree": "Bánh Thưởng Hồi Năng",
    "Meow's Grace": "Miêu Thần Diệu Ân",
    "Spark of Finality": "Hỏa Hoa Cứu Cực",
    "Pulsing Cinder": "Cộng Chấn Minh Hỏa",
    "Knight Oath: Skyfall": "Kỵ Thệ: Thiên Khung Băng Lạc",
    "Perfect Spiral": "Vòng Xoáy Hoàn Hảo",
    "Wolfpack Coordination": "Bầy Sói Phối Hợp",
    "Alpha Wolf": "Đầu Sói",
    "Vector: Solidifying": "Vector: Cố Hóa",
    "Blizzard: Stack": "Thường Lượng: Điệp Gia",
    "Firefly Glow: Radiance": "Huỳnh Lưu: Phất Chiếu",
    "Firefly Glow: Luminary": "Huỳnh Lưu: Lũng Quang",
    "Chill Forecast": "Dự Báo Hàn Băng",
    "Unstoppable March": "Tiến Bước Trong Bão Tuyết",
    "Freezing Stasis": "Sương Ngưng Trệ Đóng Băng",
    "Ultimatum": "Tối Hậu Thư",
    # TowerDefensePotential
    "Ardent Trigger": "Cò Súng Rực Lửa",
    "Precise Temperature Control": "Chuẩn Xác Khống Nhiệt",
    "Dominant Firepower": "Hỏa Lực Áp Đảo",
    "Scattering Waltz": "Vũ Bước Tản Mác",
    "Creed of Fortification": "Kiên Bích Tín Điều",
    "Brilliant Relay": "Tiếp Sức Tuyệt Diệu",
    "Holy Domain": "Thánh Quang Lĩnh Vực",
    "Mystery of Gyration": "Áo Nghĩa Hồi Chuyển",
    "Skill Charge": "Tích Năng Kỹ Năng",
    "Extended Shift": "Tăng Ca Trực Chiến",
    "High Risk": "Nguy Cơ Cao",
    "Phantom Waltz": "Huyễn Vũ Bộ",
    "Gloomy Veil": "Mây Mù Ảm Đạm",
    "Raging Blizzard": "Bạo Phong Mạn Tuyết",
    "Cold Snap": "Hàn Khí Bất Chợt",
    "Wind Slash": "Đoạn Phong Trảm",
    # SubNoteSkill (Disc Melodies)
    "Melody of Pummel": "Khúc Âm Cường Công",
    "Melody of Luck": "Khúc Âm May Mắn",
    "Melody of Burst": "Khúc Âm Bộc Phá",
    "Melody of Stamina": "Khúc Âm Thể Lực",
    "Melody of Focus": "Khúc Âm Chuyên Chú",
    "Melody of Skill": "Khúc Âm Kỹ Xảo",
    "Melody of Ultimate": "Khúc Âm Tuyệt Kỹ",
    "Melody of Aqua": "Khúc Âm Thủy Sắc",
    "Melody of Ignis": "Khúc Âm Hỏa Diễm",
    "Melody of Ventus": "Khúc Âm Phong Cuộn",
    "Melody of Terra": "Khúc Âm Địa Trọng",
    "Melody of Lux": "Khúc Âm Quang Diệu",
    "Melody of Umbra": "Khúc Âm Ám Ảnh",
    # VampireTalent
    "Destiny's Gift": "Quà Tặng Định Mệnh",
    "Hand of Destiny": "Bàn Tay Định Mệnh",
    "EXP Magnet": "Nam Châm Kinh Nghiệm",
    "HP Restoration": "Hồi Phục Sinh Mệnh",
    "ATK Enhancement": "Cường Hóa Tấn Công",
    "Crit Enhancement": "Cường Hóa Bạo Kích",
    "HP Enhancement": "Cường Hóa HP",
    "Energy Restoration": "Hồi Phục Năng Lượng",
    "Cooldown Reduction": "Giảm Hồi Chiêu",
    "Abundant EXP": "Kinh Nghiệm Phong Phú",
    "Lucky Star": "Ngôi Sao May Mắn"
}

for k, v in boss_affixes_map.items():
    register_term(k, v, "Kỹ Năng & Từ Tố Boss / Hệ Thống Phụ", "Pillar 1 & 4")

# =========================================================================
# 4. HỒ SƠ, LỒNG TIẾNG & TRANG PHỤC NHÂN VẬT (Pillar 2)
# =========================================================================
char_p2_map = {
    # Missing Character names & NPCs
    "Angie": "Angie",
    "Iori": "Iori",
    "Bloc": "Bloc",
    "Spellbound Golem (Left Hand)": "Cự Tượng Ma Thị (Tay Trái)",
    "Spellbound Golem (Right Hand)": "Cự Tượng Ma Thị (Tay Phải)",
    # Character tags
    "Collector": "Người Thích Thu Thập",
    "Steady": "Vững Vàng Từng Bước",
    "Adventurous": "Nhà Thám Hiểm",
    "Creative": "Giàu Trí Tưởng Tượng",
    "Inquisitive": "Ham Học Hỏi",
    # Voice line cues (Natural pure Vietnamese)
    "Ultimate Battle Cry": "Tuyên Ngôn Tuyệt Kỹ",
    "Character Down": "Kiệt Sức Gục Ngã",
    "Potential Acquired": "Khai Mở Tiềm Năng",
    "Monolith: Ascension Begins": "Tháp Sao: Bắt Đầu Thám Hiểm",
    "Monolith: Ascension Begins (New Difficulty)": "Tháp Sao: Khám Phá Độ Khó Mới",
    "Monolith: Ascension Begins (New Type)": "Tháp Sao: Khám Phá Loại Mới",
    "Monolith Shop": "Cửa Hàng Tháp Sao",
    "Monolith: Safe Room": "Phòng Nghỉ An Toàn Tháp Sao",
    "Monolith: Event": "Sự Kiện Tháp Sao",
    "Monolith: Battle Ended": "Tháp Sao: Trận Đấu Kết Thúc",
    "Greetings": "Lời Chào",
    "Home Screen Interaction": "Tương Tác Màn Hình Chính",
    "Home Screen Interaction: Affinity": "Tương Tác Thân Mật",
    "Home Screen Interaction: Idle": "Tương Tác Chờ",
    "Home Screen Interaction: Inactive": "Tương Tác Treo Máy Lâu",
    "Home Screen Interaction: Repeated Input": "Tương Tác Nhấp Liên Tục",
    "Listen to a Common Runic Disc": "Lắng Nghe Khắc Nguyện Thường",
    "Listen to a Unique Runic Disc": "Lắng Nghe Khắc Nguyện Đặc Biệt",
    "Memory Snapshot Unlocked": "Mở Khóa Khoảnh Khắc Hồi Ức",
    "New Stance Unlocked": "Mở Khóa Dáng Vẻ Mới",
    "Significant Trekker Growth": "Lữ Khách Trưởng Thành Vượt Bậc",
    "Trekker Development": "Bồi Dưỡng Lữ Khách",
    "Motto": "Châm Ngôn Cá Nhân",
    "Affirmative": "Đồng Ý",
    "Disagreeing": "Không Đồng Ý",
    "Angry": "Giận Dỗi",
    "Happy": "Vui Vẻ",
    "Sad": "Buồn Bã",
    "Confused": "Bối Rối",
    "Questioning": "Thắc Mắc",
    "Sigh": "Thở Dài",
    "Excited": "Hào Hứng",
    "Appreciating the Gift": "Cảm Ơn Quà Tặng",
    "Defeated": "Thất Bại",
    "Victory": "Thắng Lợi",
    "Entering Combat": "Xuất Trận",
    "First Meeting": "Lần Đầu Gặp Gỡ",
    "Meeting Again": "Tái Ngộ",
    # Character Skins
    "Playful Innocence": "Ngây Thơ Tinh Nghịch",
    "Ease Into an Unhurried Summer": "Hè Về An Yên",
    "This Is My Justice!": "Đây Là Chính Nghĩa Của Ta!",
    "Shining Bright, Spirits High": "Ánh Sáng Rực Rỡ, Ý Chí Sục Sôi",
    "The 1/365th of You": "Một Phần 365 Của Em",
    "Drifting Together on Gentle Waves": "Dập Dềnh Làn Sóng Êm",
    "Lingering Sunlight": "Dư Vị Nắng Ấm",
    "Feeling Spicy? Take the Heat!": "Thử Một Chút Cay Nhé!",
    "Resting in the Lush Greenhouse": "Nghỉ Ngơi Nơi Nhà Kính Xanh",
    "Feast of Fortune March": "Khúc Hành Quân Vận May Ẩm Thực",
    "When Distant Winds Rise": "Khi Ngọn Gió Phương Xa Nổi Lên",
    "The Formula for Victory": "Phương Trình Chiến Thắng",
    "Princess of the Wondrous Wilds": "Công Chúa Xứ Rừng Diệu Kỳ",
    "The Gift of Falling Snow": "Món Quà Tuyết Rơi",
    "My Stage, My Creation": "Sân Khấu Do Chính Tôi Dựng Xây",
    "Rookie Hero Reporting In": "Tân Binh Dũng Giả Đến Trình Diện",
    "Tipsy Daydream": "Mộng Ngày Chếnh Choáng",
    "Rippling Void of the Darkest Heartbreak": "Sóng Gương Lấp Lánh ☆ Nỗi Đau Đêm Tối",
    "A Dip of Fresh Summer": "Giọt Sương Đầu Hè",
    "Probation Period Cleared!": "Vượt Qua Kỳ Thử Việc!",
    "Cocoa Night Sweetheart": "Đêm Ca Cao Ngọt Ngào",
    "Carefree in the Golden Glow": "Thong Dong Hoàng Hôn",
    "Crimson Reflection of Queen of Hearts": "Nữ Hoàng Cơ Trong Gương",
    "A Taste of Summer All to Herself": "Vị Hè Riêng Một Góc Trời",
    "When Morning Glories Bloom, Her Eyes Open": "Hoa Bìm Nở Rộ, Thiếu Nữ Tỉnh Giấc",
    "Mellow Bass Echo": "Tiếng Bass Ngọt Ngào",
    "Promise Beyond the Thaw": "Lời Hẹn Khi Tuyết Tan",
    "Quirky Tea Party": "Tiệc Trà Tinh Quái",
    "Valentine's Day Mistique": "Mistique Tình Nhân"
}

for k, v in char_p2_map.items():
    register_term(k, v, "Hồ Sơ, Lồng Tiếng & Trang Phục Nhân Vật", "Pillar 2")

# Also auto-expand Default and Awakened skins for characters
character_list = [
    "Amber", "Tilia", "Kasimira", "Firenze", "Iris", "Noya", "Shimiao", "Chaton", "Firefly", "Ridge",
    "Jinglin", "Coronis", "Nanoha", "Canace", "Ann", "Freesia", "Flora", "Teresa", "Donna", "Minova",
    "Nazuka", "Fuyuka", "Mistique", "Eleanor", "Allie", "Sparkla", "Chixia", "Cosette", "Wraith",
    "Chitose", "Otoha", "Caramel", "Gerie", "Laru", "Shia", "Nazuna", "Karin", "Willow",
    "Snowish Laru", "Springseek Coronis", "Suntide Willow"
]
for ch in character_list:
    register_term(f"{ch}: Default", f"{ch}: Mặc Định", "Trang Phục Nhân Vật", "Pillar 2")
    register_term(f"{ch}: Awakened", f"{ch}: Thức Tỉnh", "Trang Phục Nhân Vật", "Pillar 2")

# =========================================================================
# 5. ĐỊA DANH, HẸN HÒ & CỐT TRUYỆN PHỤ (Pillar 3)
# =========================================================================
p3_map = {
    # DatingLandmark
    "The Academy": "Học Viện",
    "Hot Spring Resort": "Khu Nghỉ Dưỡng Suối Nước Nóng",
    "The Cave": "Hang Động Bí Ẩn",
    "The Dessert Shop": "Tiệm Đồ Ngọt",
    "The Market": "Khu Chợ Sầm Uất",
    "The Port": "Bến Cảng",
    # NPC & Machinery
    "Enhancement Machine": "Máy Cường Hóa",
    # NPCAffinityPlot
    "The Lonely Clerk": "Nhân Viên Cô Đơn",
    "Rehired": "Tái Gia Nhập",
    "The Pure-White Angel": "Thiên Thần Thuần Khiết",
    "Healthy Diet": "Chế Độ Ăn Khỏe Mạnh",
    "The Demon's Temptation": "Sự Cám Dỗ Của Ác Ma",
    "Written by Fate": "Định Mệnh An Bài",
    "The Demon's Challenge": "Lời Khiêu Chiến Của Ác Ma",
    "A Journey Between the Pages": "Chuyến Du Hành Trang Sách"
}

for k, v in p3_map.items():
    register_term(k, v, "Địa Danh, Hẹn Hò & Cốt Truyện Phụ", "Pillar 3")

# =========================================================================
# 6. HỆ THỐNG, THẾ LỰC, GACHA & CỬA HÀNG (Pillar 4)
# =========================================================================
p4_map = {
    # Factions & Lore
    "Nova Empire": "Đế Quốc Nova",
    "Nova Dorra": "Đồng Dorra Nova",
    "Operation: Shadow Siege": "Chiến Dịch Vây Bắt Bóng Đêm",
    "Startup Incentive Fund": "Quỹ Khởi Nghiệp",
    "Special Check-In": "Điểm Danh Đặc Biệt",
    "Event Shop": "Cửa Hàng Sự Kiện",
    "Showcase": "Tủ Trưng Bày",
    # Gacha Banners & Types
    "Departure Banner": "Kỳ Chiêu Mộ Khởi Hành",
    "Limited Trekker Banner": "Kỳ Chiêu Mộ Lữ Khách Giới Hạn",
    "Permanent Trekker Banner": "Kỳ Chiêu Mộ Lữ Khách Thường",
    "Limited Disc Banner": "Kỳ Chiêu Mộ Đĩa Nhạc Giới Hạn",
    "Permanent Disc Banner": "Kỳ Chiêu Mộ Đĩa Nhạc Thường",
    "Boss's Regulars": "Hành Trình Tháp Sao",
    "Mirroring the Jade's Ideal": "Huy Ánh Bích Ngọc",
    "Sniper of the Meowverse": "Xạ Thủ Thứ Nguyên Mèo",
    "Stardust Rising in the Light": "Tinh Sa Vút Bay Trong Ánh Sáng",
    "A Fateful Encounter": "Kỳ Ngộ Định Mệnh",
    "Heartfelt Messages, Delivered on Time": "Tấm Lòng Trao Gửi, Đúng Giờ Chuyển Trao",
    "A Breezy Romance": "Gió Thoảng Dịu Êm Hương Nồng Nàn",
    "The Promise of Melting Snow": "Tuyết Tan Mầm Nở",
    "With Graceful Steps, Elegance Arrives": "Vũ Điệu Thanh Tao, Tiểu Thư Xuất Hiện",
    "Bathed in Warm Smiles, We Linger": "Đắm Chìm Trong Nụ Cười Ấm Áp",
    "The Ultimate Answer": "Đáp Án Hoàn Hảo Cuối Cùng",
    "Silver Shattering the Dark": "Ngân Thương Xuyên Màn Đêm",
    "Blades Beneath the Moon": "Đao Ảnh Trăng Đêm",
    "Where Night Blossoms Fade": "Trăng Lặn Nơi Tàn Hoa Dạ Anh",
    "Tide to the Full Moon": "Triều Dâng Trăng Tròn",
    "Bloom to the Bright Sun": "Sóng Hoa Hướng Dương",
    "Holy Night Gift Rush!": "Đại Chiến Tặng Quà Đêm Thánh!",
    "Tipsy Wisteria Dreams": "Trà Say Hương Tử Đằng",
    "Your Heart in Meow Sights": "Đã Nhắm Chuẩn Trái Tim Em",
    "If Only I Could Touch the Stars": "Chạm Vào Muôn Ánh Sao Rơi",
    "A Heart-Tuned Melody": "Định Âm Dây Đàn",
    "Joy Sets Sail, Wishes Aloft": "Khinh Khí Cầu Nguyện Ước Khởi Hành",
    "Afternoon Glimmer into the Green": "Ánh Chiều Rọi Giấc Mộng Xanh",
    "Fireworks Dazzling the Night": "Pháo Hoa Rực Rỡ Đêm Sao",
    "Toward Her Heart's Desire": "Bay Đến Thế Giới Hằng Mơ",
    "Innocent Dream Untouched": "Giấc Mộng Thơ Ngây Thuần Khiết",
    "Brilliant Ideas, Crafted by Hand": "Trí Tưởng Tượng Diệu Kỳ Gửi Nơi Thủ Công",
    "Springlight Intoxication": "Say Nắng Ngày Xuân",
    "Moon upon Still Waters": "Trăng Soi Mặt Nước Đầm Trong",
    "Lilies Whisper Through Haze": "Hương Bách Hợp Trong Sương",
    "Ocean Meets the Sky": "Biển Trời Cùng Sắc",
    "Tinges of Rainbow": "Sóng Biếc Nhuộm Sắc Cầu Vồng",
    "Ode of the Kingdom of Fries": "Bài Ca Vương Quốc Khoai Tây Chiên",
    "Fresh Affection Awakes": "Vấn Vương Chớm Nở Như Giấc Mơ",
    "Rippling Waves, a Touch so Gentle": "Sóng Nước Lăn Tăn Đầu Ngón Tay",
    "Opening Act": "Khởi Đầu May Mắn",
    # Shop Items & Currencies
    "Cerulean Ticket": "Vé Thanh Không",
    "Sprout Ticket": "Vé Manh Nha",
    "Gold Disc": "Đĩa Vàng Kim",
    "Silver Disc": "Đĩa Bạc",
    "Star Emblem Polisher": "Dung Dịch Đánh Bóng Huy Hiệu Tinh Tú",
    "Senior's Travel Journal": "Nhật Ký Lữ Hành Tiền Bối",
    "Backstage Ragged Hat": "Mũ Cũ Hậu Trường",
    "Count's Rewards": "Phần Thưởng Của Nam Tước",
    "Faint Wick": "Bấc Đèn Tàn",
    "Eerie Breath": "Tàn Khí Quái Dị",
    "Duloos Breath": "Tàn Khí Duloo",
    "Common Gift Box": "Hộp Quà Thường",
    "Everbright Wishes: Stardust": "Doanh Nguyệt Tinh Nguyện: Tinh Sa",
    "Everbright Wishes: Ascent": "Doanh Nguyệt Tinh Nguyện: Phan Đăng",
    "Stardust": "Tinh Sa",
    "Ascent": "Phan Đăng",
    "Forest Elf Fang": "Nanh Vuốt Sâm Linh",
    "Crimson Tempter": "Thệ Nghiệt Giáng Hoa",
    "Colossus Core": "Lõi Cự Tượng",
    "Wrath Beauty": "Thịnh Nộ Mỹ Nhân",
    "Radiant Feather Crown": "Vương Miện Hoàng Vũ",
    "Monster Material": "Nguyên Liệu Quái Vật",
    "Skill Cartridge": "Băng Đạn Kỹ Năng",
    "Gift Crafting": "Chế Tạo Quà Tặng",
    # Agent Commission Tabs
    "An Urgent": "Ủy Thác Khẩn Cấp",
    "Community Service": "Trợ Thủ Cộng Đồng",
    "Mystic Quest": "Thám Hiểm Bí Cảnh",
    "Stellaroid Tracing": "Truy Vết Tinh Hài",
    "Cartridge Recycling": "Thu Hồi Băng Đạn",
    # Mini-Games & Features
    "Super Flush": "Đại Đồng Hoa",
    "Flush": "Đồng Hoa",
    "Mini Flush": "Thuần Sắc",
    "Double Triplets": "Song Tam Điêu",
    "Full House": "Cù Lũ",
    "Port Defense": "Phòng Vệ Cảng Khẩu",
    "Briefcase": "Cặp Tài Liệu",
    "Candy Box": "Hộp Kẹo",
    "Intel Scroll": "Cuộn Tình Báo",
    "Bug Device": "Thiết Bị Nghe Lén",
    "Safe": "Két Sắt",
    "Symphony": "Giao Hưởng Khúc",
    "Waltz": "Vũ Khúc Luân Vũ",
    "Crunchy Shaved Ice": "Đá Bào Giòn Tan",
    "Large Pep Pep Juice": "Nước Năng Lượng Pep Pep Lớn",
    "Growth Inhibitor": "Thuốc Ức Chế Cỏ Dại",
    "Canned Stormcloud": "Hũ Mây Giông Đóng Hộp",
    # Honors & Badges
    "Novice Tyrant": "Ma Vương Tập Sự",
    "Guardian of Ash": "Ngọn Gió Khu Tro Tàn",
    "Hero of Waterway": "Anh Hùng Cầu Thủy Đạo",
    "Petal Savior": "Nhà Tài Trợ Hoa Lệnh",
    "Blooming Star": "Quý Khách Lữ Đoàn",
    "Top Performer": "Nhân Viên Ưu Tú",
    "Light Catcher": "Người Nhặt Ánh Sáng",
    "Chasing the Phantom": "Truy Vết Bóng Ma",
    "Wishmaster": "Bậc Thầy Ước Nguyện",
    "Daisy Reverie": "Ký Ức Hoa Cúc",
    "Goodbye Tyrant": "Tạm Biệt Ma Vương",
    "Kitty Seeker": "Chuyên Gia Tìm Mèo",
    "Gallant Rider": "Cộng Sự Chính Nghĩa",
    "Founding Partner": "Đối Tác Khởi Nghiệp",
    "Care-it-all": "Quản Gia Hoàng Kim",
    "Star Reacher": "Bạn Đồng Hành Đoạt Sao",
    "Hotpot Patrol": "Đồng Đội Ăn Lẩu",
    "Darker Than Dark": "Khế Ước Giả Bóng Đêm",
    "Best Playmate": "Bạn Chơi Số Một"
}

for k, v in p4_map.items():
    register_term(k, v, "Hệ Thống, Gacha & Cửa Hàng", "Pillar 4")

# =========================================================================
# 7. FORBIDDEN RULES EXTENSION
# =========================================================================
new_forbidden_rules = {
    "Thành cổ Cây bụi": "Pháo Đài Chuột Bụi (Citadel Shrubshrew)",
    "Bột chắc chắn": "Cầu Thủ Vạm Vỡ (Sturdy Batter)",
    "Tháng ba không thể ngăn cản": "Tiến Bước Trong Bão Tuyết (Unstoppable March)",
    "chiến binh bụi rậm": "Chiến Binh Chuột Bụi (Shrubshrew Warrior)",
    "Lời thề hiệp sĩ: Skyfall": "Kỵ Thệ: Thiên Khung Băng Lạc (Knight Oath: Skyfall)",
    "Bão tuyết: Ngăn xếp": "Thường Lượng: Điệp Gia (Blizzard: Stack)",
    "Vector: kiên cố hóa": "Vector: Cố Hóa (Vector: Solidifying)",
    "Dự báo thời tiết lạnh": "Dự Báo Hàn Băng (Chill Forecast)",
    "Đom đóm phát sáng: Rạng rỡ": "Huỳnh Lưu: Phất Chiếu (Firefly Glow: Radiance)",
    "Đom đóm phát sáng: Ánh sáng": "Huỳnh Lưu: Lũng Quang (Firefly Glow: Luminary)",
    "trạng thái đóng băng": "Sương Ngưng Trệ Đóng Băng (Freezing Stasis)",
    "hộp kẹo": "Hộp Kẹo (Candy Box)",
    "tối hậu thư": "Tối Hậu Thư (Ultimatum)",
    "xoắn ốc hoàn hảo": "Vòng Xoáy Hoàn Hảo (Perfect Spiral)"
}

updated_forbidden = dict(existing_forbidden)
for wrong, correct in new_forbidden_rules.items():
    updated_forbidden[wrong] = correct

# Merge into master glossary terms
updated_terms = dict(existing_terms)
updated_terms.update(new_terms_dict)

print(f"\nSummary of term expansion:")
print(f"  Existing terms in master_glossary: {len(existing_terms)}")
print(f"  New terms added: {len(new_terms_dict)}")
print(f"  Total terms in updated master_glossary: {len(updated_terms)}")
print(f"  Existing forbidden rules: {len(existing_forbidden)}")
print(f"  Updated forbidden rules: {len(updated_forbidden)}")

# Save updated config/master_glossary.json
updated_master_data = {
    "terms": updated_terms,
    "forbidden": updated_forbidden
}

with open(MASTER_GLOSSARY_PATH, "w", encoding="utf-8") as f:
    json.dump(updated_master_data, f, ensure_ascii=False, indent=2)

print(f"\nSuccessfully wrote updated master glossary to {MASTER_GLOSSARY_PATH}")

# Save Survey Report to reports/glossary_survey_report.json
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
report_data = {
    "report_title": "Báo Cáo Khảo Sát Từ Điển & Chuẩn Hóa Thuật Ngữ Stella Sora",
    "pillars_surveyed": [
        "c:\\YostarGames\\StellaSora_EN\\StellaSora_VietHoa\\work\\batches\\pillar1_dungeons_monsters.json",
        "c:\\YostarGames\\StellaSora_EN\\StellaSora_VietHoa\\work\\batches\\pillar2_voices_characters.json",
        "c:\\YostarGames\\StellaSora_EN\\StellaSora_VietHoa\\work\\batches\\pillar3_story_dating_quests.json",
        "c:\\YostarGames\\StellaSora_EN\\StellaSora_VietHoa\\work\\batches\\pillar4_system_gacha_shops.json"
    ],
    "statistics": {
        "existing_terms_count": len(existing_terms),
        "new_terms_added_count": len(new_terms_dict),
        "total_terms_count": len(updated_terms),
        "forbidden_rules_count": len(updated_forbidden)
    },
    "categories_summary": {
        cat: {
            "pillar": data["pillar"],
            "total_terms": data["count"],
            "new_terms": data["new_count"]
        }
        for cat, data in survey_categories.items()
    },
    "new_terms_sample_by_category": {
        cat: [t for t in data["terms"] if t["is_new"]][:15]
        for cat, data in survey_categories.items()
    },
    "forbidden_calques_added": new_forbidden_rules
}

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)

print(f"Successfully saved survey report to {REPORT_PATH}")
