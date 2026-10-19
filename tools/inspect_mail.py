#!/usr/bin/env python3
"""Inspect MailTemplate table entries."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['MailTemplate']
    print(f"Total MailTemplate entries: {len(items)}")

    # Check some samples
    for it in items[:40]:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it['vi_current']
        print(f"[{k}] EN: {en}")
        if cn:
            print(f"  CN: {cn}")
        print(f"  VI: {vi}")

if __name__ == '__main__':
    main()
