#!/usr/bin/env python3
import json
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from polish_skills_module import polish_skill_text

with open(ROOT / 'work' / 'polish' / 'unique_mainskill.json', 'r', encoding='utf-8') as f:
    main_items = json.load(f)
with open(ROOT / 'work' / 'polish' / 'unique_secskill.json', 'r', encoding='utf-8') as f:
    sec_items = json.load(f)

forbidden_patterns = [
    (r'\b(Aqua|Ignis|Ventus|Terra|Lux|Umbra)\b', 'Raw element name'),
    (r'có thể được', 'có thể được'),
    (r'sẽ tăng|sẽ giảm|sẽ gây|sẽ cấp', 'sẽ + V'),
    (r'hãy ', 'hãy'),
    (r'thiệt hại', 'thiệt hại'),
    (r'Lính của họ', 'Lính của họ'),
    (r'mục tiêu ưu tú', 'mục tiêu ưu tú'),
    (r'ngăn xếp|mỗi chồng', 'ngăn xếp / mỗi chồng'),
    (r'sử dụng (?:một )?kỹ năng', 'sử dụng kỹ năng'),
    (r'Main Lữ khách', 'Main Lữ khách'),
    (r'Support Lữ khách', 'Support Lữ khách'),
]

for name, items in [('MainSkill', main_items), ('SecondarySkill', sec_items)]:
    descs = [it for it in items if it['key'].endswith('.2')]
    issues = 0
    for it in descs:
        pol = polish_skill_text(it['vi_current'], it['en'])
        for pat, desc in forbidden_patterns:
            m = re.findall(pat, pol, re.I)
            if m:
                issues += 1
                print(f"[{name}] {it['key']} has {desc}: {m}")
                print(f"  EN: {it['en']}")
                print(f"  POL: {pol}")
    print(f"{name}: {len(descs)} checked, {issues} quality issues found.")
