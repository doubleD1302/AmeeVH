#!/usr/bin/env python3
"""Scan all UIText entries for translation patterns that need improvement."""

import json
import re
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_uitext.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    # Let's inspect items where EN is short (buttons, titles) vs long (descriptions, guides)
    # Check if any Vietnamese string has suspicious words
    bad_words = [
        'sao nhổ', 'lao động', 'thăng thiên', 'tài năng', 'phụ kiện',
        'mã thông báo', 'kỷ lục của bạn', 'hành trình của bạn',
        'chúng tôi có thể biết tên', 'khóa được nhập', 'bút def',
        'mất khả năng', 'spd', 'thực hiện việc', 'bị chôn vùi',
        'nó giải phóng', 'được coi là', 'ở một mình', 'phân loại thành:',
        'khoản trợ cấp', 'phím này', 'ảnh chụp nhanh bộ nhớ',
        'chế độ máy bong bóng', 'đĩa này hiện đang'
    ]

    found = []
    for it in items:
        vi_lower = it['vi'].lower()
        matched = [w for w in bad_words if w in vi_lower]
        if matched:
            found.append((it, matched))

    print(f"Total matched UIText entries: {len(found)}")
    for it, matched in found[:30]:
        print(f"[{it['key']}] Matched: {matched}")
        print(f"   EN: {it['en']}")
        print(f"   CN: {it['cn']}")
        print(f"   VI: {it['vi']}")

if __name__ == '__main__':
    main()
