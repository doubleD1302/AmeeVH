#!/usr/bin/env python3
"""Audit DictionaryDiagram and MailTemplate tables completely."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    entries = root / 'work' / 'research' / 'data_en_original' / 'entries'

    # Load CN sources
    dict_cn = json.load(open(entries / '00770_0x11a828a290791d7f.bin', encoding='utf-8'))
    mail_cn = json.load(open(entries / '00810_0x40118cbd54257e0f.bin', encoding='utf-8'))

    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dict_items = []
    for it in data['DictionaryDiagram']:
        k = it['key']
        dict_items.append({
            'key': k,
            'en': it['en'],
            'cn': dict_cn.get(k, ''),
            'vi': it['vi_current']
        })

    mail_items = []
    for it in data['MailTemplate']:
        k = it['key']
        mail_items.append({
            'key': k,
            'en': it['en'],
            'cn': mail_cn.get(k, ''),
            'vi': it['vi_current']
        })

    with open(root / 'work' / 'polish' / 'audit_dict.json', 'w', encoding='utf-8') as f:
        json.dump(dict_items, f, ensure_ascii=False, indent=2)

    with open(root / 'work' / 'polish' / 'audit_mail.json', 'w', encoding='utf-8') as f:
        json.dump(mail_items, f, ensure_ascii=False, indent=2)

    print(f"Dumped {len(dict_items)} Dict items and {len(mail_items)} Mail items.")

if __name__ == '__main__':
    main()
