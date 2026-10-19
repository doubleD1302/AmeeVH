#!/usr/bin/env python3
"""Inspect Word table entries and find clunky/machine-translated phrases."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    words = data['Word']
    print(f"Total Word entries: {len(words)}")

    # Let's inspect all items or look for descriptions
    # Note Word keys are typically Word.X.1 (name) and Word.X.2 (description)
    for it in words:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it['vi_current']
        # Let's print descriptions (usually .2) or any suspicious ones
        if k.endswith('.2') or any(w in vi.lower() for w in ['spd', 'lao động', 'được', 'bị', 'khi', 'giảm', 'tăng']):
            print(f"[{k}] EN: {en}")
            if cn:
                print(f"  CN: {cn}")
            print(f"  VI: {vi}")

if __name__ == '__main__':
    main()
