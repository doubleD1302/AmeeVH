#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname in ['Item', 'Skill', 'EffectDesc']:
    items = dataset[tname]
    print(f"==================================================")
    print(f"TABLE: {tname} ({len(items)} items)")
    print(f"==================================================")
    
    # Check passive / clunky / raw english
    clunky_patterns = [
        r'có thể được',
        r'được sử dụng',
        r'được kích hoạt',
        r'bị gây ra',
        r'được trang bị',
        r'sẽ (?:tăng|giảm|hồi phục|gây)',
        r'của mình',
        r'hãy ',
        r'thiệt hại',
        r'nguyên khối',
        r'ưu tú',
        r'Kỹ Năng Chính|Kỹ năng chính',
        r'Kỹ Năng Hỗ Trợ|Kỹ năng hỗ trợ',
        r'Lữ khách hỗ trợ',
        r'Đĩa than',
        r'Ghi âm',
        r'Kỷ lục',
        r'người đi bộ|người đi phượt',
        r'\bAqua\b|\bIgnis\b|\bVentus\b|\bTerra\b|\bLux\b|\bUmbra\b',
        r'tài năng tiềm ẩn',
        r'chôn vùi',
        r'sâu nhất của tâm hồn',
        r'sao nhổ',
        r'giải phóng những tài năng',
        r'lưu hành khắp',
        r'giấy vụn'
    ]
    
    found = 0
    for pat in clunky_patterns:
        matches = [it for it in items if re.search(pat, it['vi_current'])]
        if matches:
            found += len(matches)
            print(f"  Pattern '{pat}': {len(matches)} matches")
            for m in matches[:3]:
                print(f"    [{m['key']}]")
                print(f"      EN: {m['en']}")
                print(f"      VI: {m['vi_current']}")
    if found == 0:
        print("  No clunky patterns matched directly.")
