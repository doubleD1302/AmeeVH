#!/usr/bin/env python3
"""Detailed review of Word entries."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_word.json', 'r', encoding='utf-8') as f:
        words = json.load(f)

    print(f"Total Word entries: {len(words)}")
    
    # Check for !NONEED!
    noneed = [w for w in words if w['en'] == '!NONEED!']
    print(f"!NONEED! entries: {len(noneed)}")

    # Check non-NONEED entries
    active = [w for w in words if w['en'] != '!NONEED!']
    print(f"Active entries: {len(active)}")

    # Check entries with English abbreviations or terms in vi
    keywords = ['dmg', 'atk', 'def', 'res', 'pen', 'spd', 'auto attack', 'lao động', 'được', 'bị']
    for kw in keywords:
        matches = [w for w in active if kw in w['vi'].lower()]
        print(f"Contains '{kw}': {len(matches)}")
        for m in matches[:2]:
            print(f"   [{m['key']}] EN: {m['en'][:60]} | CN: {m['cn'][:40]} | VI: {m['vi'][:70]}")

if __name__ == '__main__':
    main()
