#!/usr/bin/env python3
"""Inspect clunky patterns, specific key issues, and stats in phase1_dataset.json."""

import json
import re
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patterns = [
        'sao nhổ', 'mất khả năng', 'lao động', 'spd', 'có thể được', 'được sử dụng',
        'được áp dụng', 'thực hiện việc', 'nó giải phóng', 'bị chôn vùi', 'chạm vào để',
        'nhấp vào', 'được cấp', 'được nhận', 'tăng lên bởi', 'giảm đi bởi', 'gây ra bởi',
        'được kích hoạt bởi', 'mỗi khi bạn', 'sau khi bạn', 'được coi là', 'ở một mình trong',
        'những tài năng', 'khi bạn', 'nếu bạn', 'của bạn', 'bởi vì', 'đã bị', 'được tạo ra',
        'chinh phục sao', 'sao hái', 'được coi như', 'được tính là', 'bị gây ra'
    ]

    for table, items in data.items():
        print(f"=== {table} ({len(items)} items) ===")
        found_any = False
        for pat in patterns:
            matches = [it for it in items if pat in it['vi_current'].lower()]
            if matches:
                found_any = True
                print(f"  Pattern '{pat}': {len(matches)} occurrences")
                for m in matches[:2]:
                    print(f"     [{m['key']}] EN: {m['en'][:50]} | VI: {m['vi_current'][:70]}")
        if not found_any:
            print("  No clunky patterns matched.")

    # Search for specific items mentioned in prompt
    print("\n=== SPECIFIC CHECKS ===")
    for table, items in data.items():
        for it in items:
            k = it['key']
            en = it['en']
            vi = it['vi_current']
            if 'star pluck' in en.lower() or 'conquest' in en.lower():
                print(f"Star/Conquest check [{table}][{k}]: EN='{en}' -> VI='{vi}'")
            if k == '1002.2' or 'incapacitated' in en.lower() or 'frozen and' in en.lower():
                print(f"Frozen check [{table}][{k}]: EN='{en}' -> VI='{vi}'")
            if 'movement spd' in en.lower() or 'reduce movement' in en.lower():
                print(f"Movement SPD check [{table}][{k}]: EN='{en}' -> VI='{vi}'")

if __name__ == '__main__':
    main()
