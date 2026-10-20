import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")
with open(glossary_file, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
forbidden_rules = master_glossary.get("forbidden", {})

batch_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b4.json")
with open(batch_path, "r", encoding="utf-8") as f:
    batch_data = json.load(f)

print(f"Glossary Surveyor B4: Scanning {len(batch_data)} clean story dialogue lines...")

# New terms identified specifically for Batch 4 (STm09, STsp, STev, DP)
NEW_B4_TERMS = {
    # 1. Absolute Mandatory Rule: Firstlight Noya -> Noya - Khải Minh
    "Firstlight Noya": "Noya - Khải Minh",
    "First Light Noya": "Noya - Khải Minh",
    "Firstlight": "Khải Minh",
    "Noya - Khải Minh": "Noya - Khải Minh",
    
    # 2. Festivals, Special Locations & Events (STev & STsp)
    "Snowish Festival": "Lễ Hội Snowish",
    "Snowish": "Snowish",
    "Snowish Tree Spirit": "Tinh Linh Cây Snowish",
    "Ghost Ship": "U Linh Hạm",
    "The Ghost Ship": "U Linh Hạm",
    "Post Haste": "Chuyển Phát Hỏa Tốc Post Haste",
    "Hexhorn Whale": "Cá Voi Lục Sừng",
    "The Hexhorn Whale": "Cá Voi Lục Sừng",
    "White Room": "Phòng Trắng",
    "The White Room": "Phòng Trắng",
    "Daisy Orphanage": "Viện Mồ Côi Daisy",
    "Dusk Arbiter": "Trọng Tài Hoàng Hôn",
    "Dusk Arbiters": "Trọng Tài Hoàng Hôn",
    "Grace Prophecies": "Lời Tiên Tri Grace",
    "Grace Prophecy": "Lời Tiên Tri Grace",
    "Nocturn Eterna": "Đêm Trường Vĩnh Cửu",
    "Soul Stones": "Hồn Thạch",
    "Soul Stone": "Hồn Thạch",
    "Second Company": "Đại Đội Hai",
    "Petal Bloom": "Mùa Hoa Nở",
    
    # 3. Core Factions & Organizations
    "Salvation Committee": "Ủy Ban Cứu Rỗi",
    "The Salvation Committee": "Ủy Ban Cứu Rỗi",
    "The Committee": "Ủy Ban Cứu Rỗi",
    "Grace Imperium": "Đế Quốc Grace",
    "The Grace Imperium": "Đế Quốc Grace",
    "Imperial Guard": "Cận Vệ Hoàng Gia",
    "Imperial Guards": "Cận Vệ Hoàng Gia",
    "White Cat Troupe": "Gánh Xiếc Mèo Trắng",
    "White Cats": "Mèo Trắng",
    "White Cat": "Mèo Trắng",
    "Boss Accord": "Hiệp Ước Của Sếp",
    "New Star Guild": "Lữ Đoàn Tân Tinh",
    "Desert Scorpions": "Bọ Cạp Sa Mạc",
    "Ashwind Clan": "Gia Tộc Tàn Phong",
    "United Harvest": "Liên Hợp Thu Hoạch",
    
    # 4. Characters & Honorifics
    "Lady Angie": "Tiểu Thư Angie",
    "Angie": "Angie",
    "Miss Caramel": "Cô Caramel",
    "Caramel": "Caramel",
    "Miss Laru": "Cô Laru",
    "Laru": "Laru",
    "Director Allie": "Giám Đốc Allie",
    "Allie": "Allie",
    "Aunt Allie": "Dì Allie",
    "Lady Firenze": "Phu Nhân Firenze",
    "Shia": "Shia",
    "Teresa": "Teresa",
    "Karin": "Karin",
    "Donna": "Donna",
    
    # 5. Colloquial / Communication De-calquing
    "commission": "nhiệm vụ ủy thác / thù lao ủy thác",
    "commissions": "nhiệm vụ ủy thác",
    "commission fee": "thù lao ủy thác",
    "commission fees": "thù lao ủy thác",
    "Do you copy?": "Nghe rõ không!?",
    "Do you copy": "Nghe rõ không!?",
    "Copy that": "Rõ rồi",
    "Copy that.": "Rõ rồi."
}

# New Forbidden Rules to guarantee anime quality & prevent raw calques
NEW_FORBIDDEN_RULES = {
    "Sơ Quang": "Khải Minh (Tuyệt đối không dùng Sơ Quang, Firstlight Noya -> Noya - Khải Minh)",
    "Noya Sơ Quang": "Noya - Khải Minh",
    "Sơ Quang Noya": "Noya - Khải Minh",
    "Firstlight Sơ Quang": "Khải Minh",
    "Bạn có sao chép không": "Nghe rõ không!?",
    "Bạn có chép không": "Nghe rõ không!?",
    "Có sao chép không": "Nghe rõ không!?",
    "sao chép không": "nghe rõ không!?",
    "sao chép điều đó": "rõ rồi / nghe rõ",
    "sao chép rồi": "rõ rồi / nghe rõ",
    "Kỵ Sĩ Hoàng Gia": "Cận Vệ Hoàng Gia (Imperial Guard -> Cận Vệ Hoàng Gia)",
    "Kim Khố Ý Chí Ân Tứ": "Đế Quốc Grace (Grace Imperium -> Đế Quốc Grace)",
    "Hoa Hồng Ủy Thác": "Thù lao ủy thác / Nhiệm vụ ủy thác (Commission / Commission Fee)",
    "U Linh Thuyền": "U Linh Hạm (Ghost Ship -> U Linh Hạm)",
    "Cá Voi 6 Sừng": "Cá Voi Lục Sừng (Hexhorn Whale -> Cá Voi Lục Sừng)",
    "Phòng Màu Trắng": "Phòng Trắng (White Room -> Phòng Trắng)",
    "Trọng Tài Chạng Vạng": "Trọng Tài Hoàng Hôn (Dusk Arbiter -> Trọng Tài Hoàng Hôn)",
    "Đêm Vĩnh Cửu": "Đêm Trường Vĩnh Cửu (Nocturn Eterna -> Đêm Trường Vĩnh Cửu)",
    "Đá Linh Hồn": "Hồn Thạch (Soul Stone -> Hồn Thạch)",
    "Đá Hồn": "Hồn Thạch (Soul Stone -> Hồn Thạch)",
    "Trại Mồ Côi Daisy": "Viện Mồ Côi Daisy (Daisy Orphanage -> Viện Mồ Côi Daisy)",
    "Trại Mồ Côi Cúc Họa Mi": "Viện Mồ Côi Daisy",
    "Bà Angie": "Tiểu Thư Angie (Lady Angie -> Tiểu Thư Angie)",
    "Quý Cô Angie": "Tiểu Thư Angie",
    "Hiệu Trưởng Allie": "Giám Đốc Allie (Director Allie -> Giám Đốc Allie)"
}

for k, v in NEW_B4_TERMS.items():
    existing_terms[k] = v

for k, v in NEW_FORBIDDEN_RULES.items():
    forbidden_rules[k] = v

master_glossary["terms"] = existing_terms
master_glossary["forbidden"] = forbidden_rules

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(master_glossary, f, indent=2, ensure_ascii=False)

# Track key entities and monitored patterns across batch 4
monitored_entities = {
    "Firstlight Noya": [r"\bFirstlight\s*Noya\b", r"\bFirst\s*Light\s*Noya\b"],
    "Noya": [r"\bNoya\b"],
    "Snowish Festival": [r"\bSnowish\s*Festival\b"],
    "Ghost Ship": [r"\bGhost\s*Ship\b"],
    "Hexhorn Whale": [r"\bHexhorn\s*Whale\b"],
    "White Room": [r"\bWhite\s*Room\b"],
    "Dusk Arbiter": [r"\bDusk\s*Arbiters?\b"],
    "Grace Prophecies": [r"\bGrace\s*Prophec(?:y|ies)\b", r"\bBook\s*of\s*Grace\s*Prophec(?:y|ies)\b"],
    "Daisy Orphanage": [r"\bDaisy\s*Orphanage\b"],
    "Nocturn Eterna": [r"\bNocturn\s*Eterna\b"],
    "Soul Stone": [r"\bSoul\s*Stones?\b"],
    "Lady Angie": [r"\bLady\s*Angie\b"],
    "Director Allie": [r"\bDirector\s*Allie\b"],
    "Miss Caramel": [r"\bMiss\s*Caramel\b"],
    "Miss Laru": [r"\bMiss\s*Laru\b"],
    "Salvation Committee": [r"\bSalvation\s*Committee\b"],
    "Grace Imperium": [r"\bGrace\s*Imperium\b"],
    "Commission (Ủy Thác)": [r"\bcommissions?\b", r"\bcommission\s*fees?\b"],
    "Radio Copy (Nghe Rõ)": [r"\bdo\s*you\s*copy\b", r"\bcopy\s*that\b"]
}

survey_entity_stats = {}
for entity_name, patterns in monitored_entities.items():
    matches = []
    for k, text in batch_data.items():
        for pat in patterns:
            if re.search(pat, text, re.I):
                matches.append({"id": k, "text": text[:100]})
                break
    target = NEW_B4_TERMS.get(entity_name) or existing_terms.get(entity_name)
    if not target:
        if "Commission" in entity_name:
            target = "nhiệm vụ ủy thác / thù lao ủy thác"
        elif "Radio Copy" in entity_name:
            target = "Nghe rõ không!? / Rõ rồi"
        else:
            target = "Quy tắc ngữ cảnh đặc biệt"
    survey_entity_stats[entity_name] = {
        "count": len(matches),
        "target_vietnamese": target,
        "examples": matches[:3]
    }

forbidden_found = {}
for k, text in batch_data.items():
    for f_pattern, f_corr in forbidden_rules.items():
        if re.search(r"\b" + re.escape(f_pattern) + r"\b", text, re.IGNORECASE):
            if f_pattern not in forbidden_found:
                forbidden_found[f_pattern] = {"correction": f_corr, "count": 0, "examples": []}
            forbidden_found[f_pattern]["count"] += 1
            if len(forbidden_found[f_pattern]["examples"]) < 3:
                forbidden_found[f_pattern]["examples"].append({"id": k, "text": text[:90]})

report = {
    "survey_date": "2026-10-20",
    "batch": "batch_10000_avg_clean_b4",
    "total_lines_scanned": len(batch_data),
    "total_master_terms": len(existing_terms),
    "new_terms_added": len(NEW_B4_TERMS),
    "total_forbidden_rules": len(forbidden_rules),
    "firstlight_noya_rule": "Noya - Khải Minh (Tuyệt đối không dùng Sơ Quang)",
    "key_entity_survey": survey_entity_stats,
    "forbidden_calques_monitored": len(forbidden_rules),
    "potential_calque_risks": forbidden_found,
    "status": "APPROVED_FOR_TRANSLATION"
}

out_report = os.path.join(viet_dir, r"work\reviews\glossary_survey_10k_b4.json")
os.makedirs(os.path.dirname(out_report), exist_ok=True)
with open(out_report, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Glossary Surveyor B4 completed successfully.")
print(f"Total Master Terms: {len(existing_terms)} (added {len(NEW_B4_TERMS)} new terms)")
print(f"Total Forbidden Rules: {len(forbidden_rules)}")
print(f"Report written to: {out_report}")
for entity_name, stats in survey_entity_stats.items():
    print(f" - {entity_name}: {stats['count']} occurrences in Batch 4")
