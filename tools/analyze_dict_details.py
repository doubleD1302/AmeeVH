#!/usr/bin/env python3
"""Detailed review of DictionaryDiagram entries."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_dict.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Total DictionaryDiagram entries: {len(items)}")

    # Check for !NONEED! or empty
    noneed = [w for w in items if w['en'] == '!NONEED!']
    print(f"!NONEED! entries: {len(noneed)}")

    # Check categories of issues
    keywords = ['thăng thiên', 'tài năng', 'mối quan hệ', 'khoản trợ cấp', 'phím này', 'phụ kiện', 'có thể được', 'được sử dụng', 'của bạn', 'nhấp vào']
    for kw in keywords:
        matches = [w for w in items if kw in w['vi'].lower()]
        print(f"Contains '{kw}': {len(matches)}")
        for m in matches[:2]:
            print(f"   [{m['key']}] EN: {m['en'][:60]} | CN: {m['cn'][:40]} | VI: {m['vi'][:70]}")

if __name__ == '__main__':
    main()
