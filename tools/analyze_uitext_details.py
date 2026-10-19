#!/usr/bin/env python3
"""Detailed review of UIText entries."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_uitext.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Total UIText entries: {len(items)}")

    # Check categories of issues
    keywords = [
        'sao nhổ', 'mất khả năng', 'lao động', 'thăng thiên', 'tài năng',
        'khoản trợ cấp', 'phím này', 'phụ kiện', 'mã thông báo', 'phát hành lại',
        'có thể được', 'được sử dụng', 'được áp dụng', 'thực hiện việc',
        'nó giải phóng', 'bị chôn vùi', 'chạm vào để', 'nhấp vào'
    ]

    for kw in keywords:
        matches = [w for w in items if kw in w['vi'].lower()]
        print(f"Contains '{kw}': {len(matches)}")
        for m in matches[:2]:
            print(f"   [{m['key']}] EN: {m['en'][:60]} | CN: {m['cn'][:40]} | VI: {m['vi'][:70]}")

if __name__ == '__main__':
    main()
