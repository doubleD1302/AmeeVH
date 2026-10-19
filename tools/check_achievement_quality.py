#!/usr/bin/env python3
"""Check Achievement table for any potential quality issues."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    achs = data['Achievement']
    issues = []
    for it in achs:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it['vi_current']

        # Check if untranslated
        if vi == en and len(en.split()) > 1:
            issues.append((k, "Untranslated", en, cn, vi))
            continue

        # Check for awkward words
        awkward = ['sao nhổ', 'lao động', 'có thể được', 'được sử dụng', 'của bạn', 'bởi vì', 'thực hiện']
        for aw in awkward:
            if aw in vi.lower():
                issues.append((k, f"Awkward word: {aw}", en, cn, vi))
                break

    print(f"Total issues in Achievement: {len(issues)}")
    for k, reason, en, cn, vi in issues[:20]:
        print(f"[{k}] {reason}")
        print(f"   EN: {en}")
        if cn:
            print(f"   CN: {cn}")
        print(f"   VI: {vi}")

if __name__ == '__main__':
    main()
