import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")
with open(glossary_file, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
forbidden_rules = master_glossary.get("forbidden", {})

batch_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b3.json")
with open(batch_path, "r", encoding="utf-8") as f:
    batch_data = json.load(f)

print(f"Glossary Surveyor B3: Scanning {len(batch_data)} clean story dialogue lines...")

# New terms identified specifically for Batch 3 (Main Story 6, 7, 8 & Phone Messages)
NEW_B3_TERMS = {
    # 1. Absolute Mandatory Rule: Firstlight Noya -> Noya - Khải Minh (Tuyệt đối không dùng Sơ Quang)
    "Firstlight Noya": "Noya - Khải Minh",
    "First Light Noya": "Noya - Khải Minh",
    "Firstlight": "Khải Minh",
    "Noya - Khải Minh": "Noya - Khải Minh",
    "Khải Minh Noya": "Noya - Khải Minh",
    
    # 2. Mandatory Factions, Organizations & Entities
    "Grace Imperium": "Đế Quốc Grace",
    "The Grace Imperium": "Đế Quốc Grace",
    "Imperial Guard": "Cận Vệ Hoàng Gia",
    "The Imperial Guard": "Cận Vệ Hoàng Gia",
    "Imperial Guards": "Cận Vệ Hoàng Gia",
    "Imperial Guard Knights": "Kỵ Sĩ Cận Vệ Hoàng Gia",
    "White Cat Troupe": "Gánh Xiếc Mèo Trắng",
    "The White Cat Troupe": "Gánh Xiếc Mèo Trắng",
    "White Cat": "Mèo Trắng",
    "White Cats": "Mèo Trắng",
    "The White Cats": "Mèo Trắng",
    "Ashwind Clan": "Gia Tộc Tàn Phong",
    "The Ashwind Clan": "Gia Tộc Tàn Phong",
    "Ashwind": "Tàn Phong",
    "Boss Accord": "Hiệp Ước Của Sếp",
    "Mirage": "Huyễn Cảnh",
    "Mirages": "Huyễn Cảnh",
    "Omnisky Aegis": "Khiên Thanh Không",
    "New Star Guild": "Lữ Đoàn Tân Tinh",
    "Salvation Committee": "Ủy Ban Cứu Rỗi",
    "Desert Scorpions": "Bọ Cạp Sa Mạc",
    "Intelligent Plants": "Thực Vật Thông Tuệ",
    "Deepsea Finance": "Tài Chính Biển Sâu",
    "United Harvest": "Liên Hợp Thu Hoạch",
    "United Harvest Philae": "Chi Nhánh Philae - Liên Hợp Thu Hoạch",
    
    # 3. Task & Radio Communication Rules (De-calquing)
    "commission": "nhiệm vụ ủy thác",
    "commissions": "nhiệm vụ ủy thác",
    "commission fee": "thù lao ủy thác",
    "commission fees": "thù lao ủy thác",
    "Do you copy?": "Nghe rõ không!?",
    "Do you copy": "Nghe rõ không!?",
    "Copy that": "Rõ rồi",
    "Copy that.": "Rõ rồi.",
    
    # 4. Key Characters & Honorifics
    "Your Majesty": "Bệ Hạ",
    "Grand Inspector": "Đại Thanh Tra",
    "Grand Inspector Matilda": "Đại Thanh Tra Matilda",
    "Inspector Nyx": "Thanh Tra Nyx",
    "Nyx": "Nyx",
    "Matilda": "Matilda",
    "Darcia": "Darcia",
    "Lady Darcia": "Phu Nhân Darcia",
    "Firenze": "Firenze",
    "Lady Firenze": "Phu Nhân Firenze",
    "Grace": "Grace",
    "Philae": "Philae",
    "Noya": "Noya",
    "Amber": "Amber",
    "Kohaku": "Kohaku",
    "Iris": "Iris",
    "Chitose": "Chitose",
    "Nazuka": "Nazuka",
    "Fuyuka": "Fuyuka",
    "Allie": "Allie",
    "Aunt Allie": "Dì Allie",
    "De Feltro": "De Feltro",
    
    # 5. Lore Locations & Concepts
    "Gold District": "Khu Vàng",
    "Silver District": "Khu Bạc",
    "Ash District": "Khu Tro",
    "Greenhouse District": "Khu Nhà Kính",
    "Lucky Oasis": "Ốc Đảo May Mắn",
    "Trekker Camp": "Doanh Trại Lữ Khách",
    "Scarlet Sights": "Cảnh Sắc Đỏ Rực",
    "New Orelian": "Tân Orelian",
    "Messis Month": "Tháng Messis",
    "Venatio Month": "Tháng Venatio",
    "Monolith Calendar Year": "Năm Lịch Cự Thạch",
    "Fenghuang Diner": "Quán Ăn Phượng Hoàng",
    "Executive Office": "Văn Phòng Chấp Hành",
    "Sky Institute": "Viện Bầu Trời",
    "Goodwind Homecare": "Chăm Sóc Gia Đình Goodwind",
    "Wishing Box": "Hộp Ước Nguyện"
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
    "Kim Khố Ý Chí Ân Tứ": "Đế Quốc Grace (Grace Imperium -> Đế Quốc Grace)"
}

for k, v in NEW_B3_TERMS.items():
    existing_terms[k] = v

for k, v in NEW_FORBIDDEN_RULES.items():
    forbidden_rules[k] = v

master_glossary["terms"] = existing_terms
master_glossary["forbidden"] = forbidden_rules

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(master_glossary, f, indent=2, ensure_ascii=False)

# Track key entities and monitored patterns across batch 3
monitored_entities = {
    "Firstlight Noya": [r"\bFirstlight\s*Noya\b", r"\bFirst\s*Light\s*Noya\b"],
    "Noya": [r"\bNoya\b"],
    "Grace Imperium": [r"\bGrace\s*Imperium\b"],
    "Imperial Guard": [r"\bImperial\s*Guards?\b"],
    "White Cat Troupe / White Cats": [r"\bWhite\s*Cats?\s*Troupe\b", r"\bWhite\s*Cats?\b"],
    "Ashwind Clan": [r"\bAshwind\s*Clan\b", r"\bAshwind\b"],
    "Mirage": [r"\bMirages?\b"],
    "Boss Accord": [r"\bBoss\s*Accord\b"],
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
    survey_entity_stats[entity_name] = {
        "count": len(matches),
        "target_vietnamese": NEW_B3_TERMS.get(entity_name, "Quy tắc ngữ cảnh đặc biệt"),
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
    "batch": "batch_10000_avg_clean_b3",
    "total_lines_scanned": len(batch_data),
    "total_master_terms": len(existing_terms),
    "new_terms_added": len(NEW_B3_TERMS),
    "total_forbidden_rules": len(forbidden_rules),
    "firstlight_noya_rule": "Noya - Khải Minh (Tuyệt đối không dùng Sơ Quang)",
    "key_entity_survey": survey_entity_stats,
    "forbidden_calques_monitored": len(forbidden_rules),
    "potential_calque_risks": forbidden_found,
    "status": "APPROVED_FOR_TRANSLATION"
}

out_report = os.path.join(viet_dir, r"work\reviews\glossary_survey_10k_b3.json")
os.makedirs(os.path.dirname(out_report), exist_ok=True)
with open(out_report, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Glossary Surveyor B3 completed successfully.")
print(f"Total Master Terms: {len(existing_terms)} (added {len(NEW_B3_TERMS)} new terms)")
print(f"Total Forbidden Rules: {len(forbidden_rules)}")
print(f"Report written to: {out_report}")
for entity_name, stats in survey_entity_stats.items():
    print(f" - {entity_name}: {stats['count']} occurrences in Batch 3")

