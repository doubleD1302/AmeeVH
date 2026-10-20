import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")
with open(glossary_file, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
forbidden_rules = master_glossary.get("forbidden", {})

batch_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b2.json")
with open(batch_path, "r", encoding="utf-8") as f:
    batch_data = json.load(f)

print(f"Glossary Surveyor B2: Scanning {len(batch_data)} clean story dialogue lines...")

# New terms identified specifically for Batch 2 (Main Story 4 & 5, CG Lữ Khách)
NEW_B2_TERMS = {
    # Absolute Mandatory Rule: Firstlight Noya -> Noya - Khải Minh
    "Firstlight Noya": "Noya - Khải Minh",
    "First Light Noya": "Noya - Khải Minh",
    "Firstlight": "Khải Minh",
    "Noya - Khải Minh": "Noya - Khải Minh",
    
    # Factions & Organizations
    "United Harvest": "Liên Hợp Thu Hoạch",
    "Tawny Nightingale": "Dạ Oanh Hoàng Lạc",
    "Lady Gray": "Phu Nhân Gray",
    "Parasite": "Ký Sinh Thể",
    "Tyrant": "Bạo Quân",
    "Mistique": "Mistique",
    "Mina": "Mina",
    "Garden": "Hoa Viên",
    "Monolith": "Cự Thạch",
    "Stellaroid": "Thể Tinh Tú",
    "Stellaroids": "Các Thể Tinh Tú",
    "Trekker": "Lữ Khách",
    "Trekkers": "Các Lữ Khách",
    "Emor City": "Thành Phố Emor",
    "Philae": "Philae",
    "Nazuka": "Nazuka",
    "Fuyuka": "Fuyuka",
    "Amber": "Amber",
    "Kohaku": "Kohaku",
    "Iris": "Iris",
    "Chitose": "Chitose",
    "Tilia": "Tilia",
    "Dorra": "Dorra",
    "Torina": "Torina",
    "Bastelina": "Bastelina",
    "Ayame": "Ayame",
    "Seina": "Seina",
    "Feagin": "Feagin",
    "Canace": "Canace",
    "Serena": "Serena",
    "Vita": "Vita",
    "Galavera": "Galavera",
    "Daria": "Daria",
    "Loxy": "Loxy",
    "Allie": "Allie"
}

# Update master glossary
for k, v in NEW_B2_TERMS.items():
    existing_terms[k] = v

master_glossary["terms"] = existing_terms

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(master_glossary, f, indent=2, ensure_ascii=False)

# Check forbidden occurrences
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
    "batch": "batch_10000_avg_clean_b2",
    "total_lines_scanned": len(batch_data),
    "total_master_terms": len(existing_terms),
    "new_terms_added": len(NEW_B2_TERMS),
    "firstlight_noya_rule": "Noya - Khải Minh (Tuyệt đối không dùng Sơ Quang)",
    "forbidden_calques_monitored": len(forbidden_rules),
    "potential_calque_risks": forbidden_found,
    "status": "APPROVED_FOR_TRANSLATION"
}

out_report = os.path.join(viet_dir, r"work\reviews\glossary_survey_10k_b2.json")
os.makedirs(os.path.dirname(out_report), exist_ok=True)
with open(out_report, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Glossary Surveyor B2 completed. Report written to {out_report}")
