#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

items = dataset['Item']
lore_items = [it for it in items if it['key'].endswith('.3')]
print(f"Total lore items (.3): {len(lore_items)}")

# Check for stiff patterns in lore items
stiff_patterns = [
    r'được phát hành bởi',
    r'có thể được',
    r'được sử dụng',
    r'bị chôn vùi',
    r'những góc sâu nhất',
    r'giấy vụn',
    r'của bạn',
    r'của mình',
    r'nó thật',
    r'nó giải phóng',
    r'khảo sát tất cả',
    r'trái đất',
    r'những người đi bộ'
]

for pat in stiff_patterns:
    matches = [it for it in lore_items if re.search(pat, it['vi_current'], re.IGNORECASE)]
    if matches:
        print(f"Pattern '{pat}': {len(matches)} matches")
        for m in matches[:2]:
            print(f"  [{m['key']}]")
            print(f"    EN: {m['en']}")
            print(f"    VI: {m['vi_current']}")
