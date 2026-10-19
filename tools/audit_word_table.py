#!/usr/bin/env python3
"""Audit Word table completely."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    cn_file = root / 'work' / 'research' / 'data_en_original' / 'entries' / '00934_0x740d729a46a8d407.bin'

    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(cn_file, 'r', encoding='utf-8') as f:
        cn_data = json.load(f)

    words = data['Word']
    out_items = []
    for it in words:
        k = it['key']
        en = it['en']
        cn = cn_data.get(k, '')
        vi = it['vi_current']
        out_items.append({
            'key': k,
            'en': en,
            'cn': cn,
            'vi': vi
        })

    out_path = root / 'work' / 'polish' / 'audit_word.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_items, f, ensure_ascii=False, indent=2)

    print(f"Dumped {len(out_items)} Word items to {out_path}")

if __name__ == '__main__':
    main()
