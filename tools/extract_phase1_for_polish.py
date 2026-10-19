#!/usr/bin/env python3
"""Extract Phase 1 tables (UIText, Word, DictionaryDiagram, MailTemplate, Achievement) for localization polish."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    p_orig = root / 'work' / 'research' / 'data_en_original' / 'entries'
    p_curr = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    out_dir = root / 'work' / 'polish'
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        'UIText': '00704_0x87cc29ac0defc2d9.bin',
        'Word': '00713_0x78b1aa32bbcf433e.bin',
        'DictionaryDiagram': '00549_0x88d705ae9564e65e.bin',
        'MailTemplate': '00589_0x2aa9f7b7887bdb4d.bin',
        'Achievement': '00494_0x5b0fc2f5fe45a572.bin'
    }

    # Also load CN references where available
    cn_refs = {}
    word_cn = root / 'work' / 'batches' / 'word_en_cn.json'
    if word_cn.exists():
        with open(word_cn, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                cn_refs[item['key']] = item.get('cn', '')

    dict_cn = root / 'work' / 'batches' / 'dictionary_diagram_en_cn.json'
    if dict_cn.exists():
        with open(dict_cn, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                cn_refs[item['key']] = item.get('cn', '')

    mail_cn = root / 'work' / 'batches' / 'mail_template_en_cn.json'
    if mail_cn.exists():
        with open(mail_cn, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                cn_refs[item['key']] = item.get('cn', '')

    ach_cn = root / 'work' / 'research' / 'all_achievements_bilingual.json'
    if ach_cn.exists():
        with open(ach_cn, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                cn_refs[item['key']] = item.get('cn', '')

    dataset = {}
    total_keys = 0

    for name, fname in tables.items():
        with open(p_orig / fname, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        with open(p_curr / fname, 'r', encoding='utf-8') as f:
            curr = json.load(f)

        dataset[name] = []
        for k, en_val in orig.items():
            if not en_val:
                continue
            curr_val = curr.get(k, en_val)
            cn_val = cn_refs.get(k, '')
            dataset[name].append({
                'key': k,
                'en': en_val,
                'cn': cn_val,
                'vi_current': curr_val
            })
            total_keys += 1

    out_file = out_dir / 'phase1_dataset.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Extracted Phase 1 dataset to {out_file}: {total_keys} total keys across {len(tables)} tables.")
    for name, items in dataset.items():
        print(f"  - {name}: {len(items)} items")

if __name__ == '__main__':
    main()
