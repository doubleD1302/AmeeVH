#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

def main():
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    items = dataset['Item']
    print(f"Item count: {len(items)}")

    patterns = [
        ('có thể được', r'có thể được'),
        ('được sử dụng', r'được sử dụng'),
        ('chôn vùi / sâu nhất của tâm hồn / sâu thẳm', r'chôn vùi|sâu nhất của tâm hồn|sâu thẳm|tiềm ẩn'),
        ('tài năng', r'tài năng'),
        ('sao nhổ', r'sao nhổ|nhổ'),
        ('tiền tệ cơ bản', r'tiền tệ cơ bản'),
        ('Đĩa than', r'đĩa than'),
        ('Đĩa nhạc', r'đĩa nhạc'),
        ('Soul Key', r'Chìa khóa'),
        ('Deepsea Finance', r'Deepsea Finance'),
        ('scrap paper', r'giấy vụn'),
        ('Star Pluck', r'Star Pluck|Đoạt Sao|Hái Sao|nhổ'),
    ]

    for label, pat in patterns:
        matches = [it for it in items if re.search(pat, it['vi_current'] + ' ' + it['en'], re.IGNORECASE)]
        print(f"[{label}]: {len(matches)} matches")
        for m in matches[:5]:
            print(f"   Key: {m['key']}")
            print(f"   EN: {m['en']}")
            print(f"   VI: {m['vi_current']}")

if __name__ == '__main__':
    main()
