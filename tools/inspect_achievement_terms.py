#!/usr/bin/env python3
"""Check specific terms in Achievement table."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    achs = data['Achievement']
    keywords = ['conquest', 'star pluck', 'ascension', 'potential', 'talent', 'record', 'reforge', 'disc', 'monolith']

    for kw in keywords:
        matches = [it for it in achs if kw in it['en'].lower()]
        print(f"\nKeyword '{kw}': {len(matches)} matches")
        for it in matches[:3]:
            print(f"  [{it['key']}] EN: {it['en']} | VI: {it['vi_current']}")

if __name__ == '__main__':
    main()
