#!/usr/bin/env python3
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

def main():
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    for tname, items in dataset.items():
        print(f"========================================")
        print(f"TABLE: {tname} (Total: {len(items)})")
        print(f"========================================")

        patterns = [
            ("có thể được", r'có thể được'),
            ("được sử dụng", r'được sử dụng'),
            ("được kích hoạt", r'được kích hoạt'),
            ("bị gây ra", r'bị gây ra'),
            ("được trang bị", r'được trang bị'),
            ("chôn vùi / sâu nhất của tâm hồn", r'chôn vùi|sâu nhất của tâm hồn'),
            ("tài năng tiềm ẩn", r'tài năng tiềm ẩn|tài năng'),
            ("sao nhổ", r'sao nhổ|nhổ'),
            ("tiền tệ", r'tiền tệ'),
            ("Đĩa than / Đĩa nhạc", r'đĩa than|đĩa nhạc'),
            ("của mình", r'của mình'),
            ("sẽ tăng / sẽ giảm", r'sẽ (?:tăng|giảm|hồi phục|gây)'),
            ("được coi là / được tính là", r'được (?:coi là|tính là)'),
        ]

        for label, pat in patterns:
            matches = [it for it in items if re.search(pat, it['vi_current'], re.IGNORECASE)]
            if matches:
                print(f"  [{label}]: {len(matches)} matches")
                for m in matches[:2]:
                    print(f"    - Key: {m['key']}")
                    print(f"      EN: {m['en']}")
                    print(f"      VI: {m['vi_current']}")

if __name__ == '__main__':
    main()
