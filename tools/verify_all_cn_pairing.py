#!/usr/bin/env python3
"""Verify 100% CN pairing across all 5 tables."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    entries = root / 'work' / 'research' / 'data_en_original' / 'entries'

    # Load CN sources
    cn_sources = {
        'UIText': json.load(open(entries / '00925_0x363690c09b175230.bin', encoding='utf-8')),
        'Word': json.load(open(entries / '00934_0x740d729a46a8d407.bin', encoding='utf-8')),
        'DictionaryDiagram': json.load(open(entries / '00770_0x11a828a290791d7f.bin', encoding='utf-8')),
        'MailTemplate': json.load(open(entries / '00810_0x40118cbd54257e0f.bin', encoding='utf-8')),
    }

    ach_cn = {}
    with open(root / 'work' / 'research' / 'all_achievements_bilingual.json', 'r', encoding='utf-8') as f:
        for it in json.load(f):
            ach_cn[it['key']] = it.get('cn', '')
    cn_sources['Achievement'] = ach_cn

    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for tbl, items in data.items():
        matched_cn = 0
        for it in items:
            k = it['key']
            cn = cn_sources[tbl].get(k, '')
            if cn:
                matched_cn += 1
        print(f"{tbl}: {matched_cn}/{len(items)} keys have direct CN match ({matched_cn*100//len(items)}%)")

if __name__ == '__main__':
    main()
