#!/usr/bin/env python3
"""Detailed analysis of all 5 tables in phase1_dataset.json."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for table_name in ['Word', 'DictionaryDiagram', 'MailTemplate', 'Achievement', 'UIText']:
        items = data[table_name]
        print(f"\n=======================================================")
        print(f"TABLE: {table_name} ({len(items)} items)")
        print(f"=======================================================")

        # Find items with specific patterns or potential issues
        issues = []
        for it in items:
            k = it['key']
            en = it['en']
            cn = it.get('cn', '')
            vi = it['vi_current']

            # Check clunky words
            lower_vi = vi.lower()
            reasons = []
            if 'lao động' in lower_vi:
                reasons.append('mất khả năng lao động')
            if 'sao nhổ' in lower_vi:
                reasons.append('sao nhổ')
            if 'spd' in lower_vi:
                reasons.append('SPD unlocalized')
            if 'có thể được' in lower_vi or 'được sử dụng' in lower_vi or 'được áp dụng' in lower_vi:
                reasons.append('passive voice')
            if 'bị gây ra' in lower_vi or 'gây ra bởi' in lower_vi:
                reasons.append('gây ra bởi')
            if 'được tạo ra bởi' in lower_vi:
                reasons.append('được tạo ra bởi')
            if 'nó giải phóng' in lower_vi or 'bị chôn vùi' in lower_vi:
                reasons.append('nó giải phóng / chôn vùi')
            if 'chạm vào để' in lower_vi or 'nhấp vào' in lower_vi:
                reasons.append('nhấp vào / chạm vào')
            if 'của bạn' in lower_vi or 'cho bạn' in lower_vi or 'khi bạn' in lower_vi:
                reasons.append('second-person pronoun excess')
            if 'thăng thiên' in lower_vi:
                reasons.append('Thăng thiên (Ascension / Trekker level)')

            if reasons:
                issues.append((k, en, cn, vi, reasons))

        print(f"Items with potential style/grammar issues: {len(issues)} / {len(items)}")
        for k, en, cn, vi, reasons in issues[:10]:
            print(f"  [{k}] ({', '.join(reasons)})")
            print(f"     EN: {en}")
            if cn:
                print(f"     CN: {cn}")
            print(f"     VI: {vi}")

if __name__ == '__main__':
    main()
