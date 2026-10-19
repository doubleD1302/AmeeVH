#!/usr/bin/env python3
"""Display all active Word items for thorough inspection."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_word.json', 'r', encoding='utf-8') as f:
        words = json.load(f)

    active = [w for w in words if w['en'] != '!NONEED!']
    print(f"Total active Word entries: {len(active)}")

    for i, w in enumerate(active):
        print(f"[{i+1}/{len(active)}] {w['key']}")
        print(f"   EN: {w['en']}")
        print(f"   CN: {w['cn']}")
        print(f"   VI: {w['vi']}")

if __name__ == '__main__':
    main()
