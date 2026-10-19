#!/usr/bin/env python3
"""Audit Achievement and UIText tables."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    entries = root / 'work' / 'research' / 'data_en_original' / 'entries'

    # Load CN sources
    uitext_cn = json.load(open(entries / '00925_0x363690c09b175230.bin', encoding='utf-8'))

    ach_cn = {}
    with open(root / 'work' / 'research' / 'all_achievements_bilingual.json', 'r', encoding='utf-8') as f:
        for it in json.load(f):
            ach_cn[it['key']] = it.get('cn', '')

    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ach_items = []
    for it in data['Achievement']:
        k = it['key']
        ach_items.append({
            'key': k,
            'en': it['en'],
            'cn': ach_cn.get(k, ''),
            'vi': it['vi_current']
        })

    uitext_items = []
    for it in data['UIText']:
        k = it['key']
        uitext_items.append({
            'key': k,
            'en': it['en'],
            'cn': uitext_cn.get(k, ''),
            'vi': it['vi_current']
        })

    with open(root / 'work' / 'polish' / 'audit_ach.json', 'w', encoding='utf-8') as f:
        json.dump(ach_items, f, ensure_ascii=False, indent=2)

    with open(root / 'work' / 'polish' / 'audit_uitext.json', 'w', encoding='utf-8') as f:
        json.dump(uitext_items, f, ensure_ascii=False, indent=2)

    print(f"Dumped {len(ach_items)} Ach items and {len(uitext_items)} UIText items.")

if __name__ == '__main__':
    main()
