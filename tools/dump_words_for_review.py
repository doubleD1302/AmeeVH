#!/usr/bin/env python3
"""Inspect all Word entries to prepare the full polish map."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_word.json', 'r', encoding='utf-8') as f:
        words = json.load(f)

    # Let's see which words need polish
    print(f"Total: {len(words)}")
    for it in words:
        k = it['key']
        en = it['en']
        cn = it['cn']
        vi = it['vi']
        # Print if active
        if en != '!NONEED!':
            print(f"{k} | EN: {en} | CN: {cn} | VI: {vi}")

if __name__ == '__main__':
    main()
