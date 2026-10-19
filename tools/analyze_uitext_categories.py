#!/usr/bin/env python3
"""Analyze UIText entries."""

import json
from pathlib import Path
from collections import Counter

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    uitext = data['UIText']
    print(f"Total UIText entries: {len(uitext)}")

    prefixes = Counter()
    for it in uitext:
        k = it['key']
        # e.g., UIText.Achievement_Type_2.1 -> prefix is Achievement
        parts = k.split('.')
        if len(parts) >= 2:
            sub = parts[1].split('_')[0]
            prefixes[sub] += 1

    print("Top 30 prefixes in UIText:")
    for pref, count in prefixes.most_common(30):
        print(f"  {pref}: {count}")

if __name__ == '__main__':
    main()
