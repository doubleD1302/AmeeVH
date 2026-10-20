import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))
glossary = json.load(open(ROOT / "config" / "master_glossary.json", encoding='utf-8'))

# Check master glossary consistency
glossary_check = [
    ("New Star Guild", "Lữ Đoàn Tân Tinh", ["Hiệp hội Ngôi sao Mới", "Hội Ngôi Sao Mới", "Bang Hội Tân Tinh"]),
    ("White Cat Troupe", "Gánh Xiếc Mèo Trắng", ["Đội Mèo Trắng", "Đoàn Mèo Trắng"]),
    ("Imperial Guard", "Cận Vệ Hoàng Gia", ["Vệ binh Hoàng gia", "Kỵ Sĩ Hoàng Gia", "Cận vệ hoàng gia"]),
    ("Ashwind Clan", "Gia Tộc Tàn Phong", []),
    ("United Harvest", "Liên Hợp Thu Hoạch", ["Thu Hoạch Thống Nhất", "Hoa Thu Hoạch"]),
    ("Firstlight Noya", "Noya - Khải Minh", ["Sơ Quang", "Noya Sơ Quang"]),
    ("Trekker", "Lữ Khách", ["Người Du Hành", "Kẻ Du Hành"]),
]

issues = []

for term_en, term_vi_correct, forbidden_variants in glossary_check:
    for k, o in orig.items():
        t = trans.get(k, "")
        for f in forbidden_variants:
            if f.lower() in t.lower():
                issues.append((k, term_en, f"Contains forbidden variant '{f}' (should be '{term_vi_correct}')", o, t))
        # Check if english term in orig but correct vi not in t
        if term_en.lower() in o.lower() and term_vi_correct.lower() not in t.lower():
            issues.append((k, term_en, f"Missing target '{term_vi_correct}' when orig has '{term_en}'", o, t))

print(f"Glossary issues found: {len(issues)}")
for iss in issues[:30]:
    print(f"[{iss[0]}] Term: {iss[1]} | Reason: {iss[2]}")
    print(f"  Orig:  {iss[3]}")
    print(f"  Trans: {iss[4]}")
