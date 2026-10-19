#!/usr/bin/env python3
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

print("=== PASSIVE VOICE & STIFF TRANSLATION AUDIT ===")
patterns = [
    (r'có thể được', 'có thể được (passive ability)'),
    (r'được sử dụng', 'được sử dụng (passive usage)'),
    (r'được kích hoạt', 'được kích hoạt (passive trigger)'),
    (r'bị gây ra', 'bị gây ra (passive inflict)'),
    (r'được trang bị', 'được trang bị (passive equip)'),
    (r'sẽ (?:tăng|giảm|hồi phục|gây)', 'sẽ + V (clunky future tense)'),
    (r'của mình', 'của mình (unnecessary possessive)'),
    (r'hãy (?:tăng|giảm|hồi)', 'hãy (machine mistranslation of increases/heals)'),
    (r'được coi là|được tính là', 'được coi là / tính là'),
    (r'tài năng tiềm ẩn', 'tài năng tiềm ẩn'),
    (r'chôn vùi', 'chôn vùi'),
    (r'sâu nhất của tâm hồn', 'sâu nhất của tâm hồn'),
    (r'sao nhổ', 'sao nhổ'),
    (r'thiệt hại', 'thiệt hại (instead of sát thương)'),
    (r'nguyên khối', 'nguyên khối (instead of Cự tháp)'),
    (r'ưu tú', 'ưu tú (instead of Tinh anh)'),
    (r'Kỹ Năng Chính|Kỹ năng chính', 'Kỹ năng chính (instead of Kỹ năng chủ lực)'),
    (r'Kỹ Năng Hỗ Trợ|Kỹ năng hỗ trợ|Lữ khách hỗ trợ', 'Kỹ năng/Lữ khách hỗ trợ (instead of Viện trợ)'),
    (r'Đĩa than', 'Đĩa than (instead of Đĩa nhạc)'),
    (r'Ghi âm', 'Ghi âm (instead of Bản ghi / Hồ sơ)'),
    (r'Kỷ lục', 'Kỷ lục (instead of Bản ghi / Hồ sơ)'),
    (r'người đi bộ|người đi phượt', 'người đi bộ / đi phượt'),
    (r'\bAqua\b|\bIgnis\b|\bVentus\b|\bTerra\b|\bLux\b|\bUmbra\b', 'Raw element names (Aqua/Ignis/etc.)')
]

for tname, items in dataset.items():
    print(f"\n--- TABLE: {tname} ({len(items)} items) ---")
    for pat, label in patterns:
        matching = [it for it in items if re.search(pat, it['vi_current'])]
        if matching:
            print(f"  {label}: {len(matching)} occurrences")
            for m in matching[:2]:
                print(f"    [{m['key']}]")
                print(f"      EN: {m['en']}")
                print(f"      VI: {m['vi_current']}")
