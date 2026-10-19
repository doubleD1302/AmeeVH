#!/usr/bin/env python3
"""Detailed inspection of Achievement table."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    achs = data['Achievement']
    print(f"Total Achievement items: {len(achs)}")

    # Show first 30 items
    for it in achs[:25]:
        print(f"[{it['key']}] EN: {it['en']}")
        if it.get('cn'):
            print(f"  CN: {it['cn']}")
        print(f"  VI: {it['vi_current']}")

if __name__ == '__main__':
    main()
