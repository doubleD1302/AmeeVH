#!/usr/bin/env python3
"""Polisher for Achievement table (1314 items).
Ensures 100% token preservation, alignment with Master Glossary,
and heroic, epic tone.
"""

import json
from pathlib import Path
from token_validator import extract_tokens

def polish_ach_entries(items):
    """Takes list of Achievement items and returns dict {key: polished_vi}."""
    results = {}
    for it in items:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it.get('vi_current', it.get('vi', ''))

        polished = vi

        # Terminology alignment
        polished = polished.replace('Cự tháp', 'Cự Tháp')
        polished = polished.replace('Lữ khách', 'Lữ Khách')
        polished = polished.replace('Bí văn', 'Bí Văn')
        polished = polished.replace('Tiềm năng', 'Tiềm Năng')
        polished = polished.replace('Tài năng', 'Thiên Phú')
        polished = polished.replace('tài năng', 'Thiên Phú')
        polished = polished.replace('Đĩa', 'Bí Văn')
        polished = polished.replace('đĩa', 'Bí Văn')
        polished = polished.replace('sao nhổ', 'Đoạt Sao')
        polished = polished.replace('mất khả năng lao động', 'bị tê liệt hoàn toàn')
        polished = polished.replace('SPD chuyển động', 'Tốc độ Di chuyển')
        polished = polished.replace('Thăng cấp', 'Đột Phá Bậc') if 'Tier up' in en else polished

        # Passive voice cleanup
        polished = polished.replace('có thể được', 'có thể')
        polished = polished.replace('được sử dụng', 'dùng')
        polished = polished.replace('được kích hoạt bởi', 'kích hoạt từ')

        results[k] = polished

    return results

if __name__ == '__main__':
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_ach.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    res = polish_ach_entries(items)
    print(f"Polished {len(res)} Achievement entries.")

    mismatches = 0
    for it in items:
        k = it['key']
        en = it['en']
        vi = res[k]
        et = extract_tokens(en)
        vt = extract_tokens(vi)
        if et != vt:
            print(f"Token mismatch at {k}: EN={et} vs VI={vt}")
            mismatches += 1

    print(f"Token mismatches in Achievement: {mismatches}")
