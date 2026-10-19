#!/usr/bin/env python3
"""Check UIText CN file 00925."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    cn_file = root / 'work' / 'research' / 'data_en_original' / 'entries' / '00925_0x363690c09b175230.bin'
    en_file = root / 'work' / 'research' / 'data_en_original' / 'entries' / '00704_0x87cc29ac0defc2d9.bin'

    with open(cn_file, 'r', encoding='utf-8') as f:
        cn_data = json.load(f)
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    print(f"UIText EN count: {len(en_data)}, CN count: {len(cn_data)}")

    # Check key overlap
    common = set(en_data.keys()) & set(cn_data.keys())
    print(f"Common keys: {len(common)} / {len(en_data)}")

    # Sample comparisons
    for k in list(common)[:10]:
        print(f"[{k}] EN: {en_data[k]} | CN: {cn_data[k]}")

    # Check 'Star Pluck Conquest'
    k_sp = 'UIText.Achievement_Type_2.1'
    if k_sp in cn_data:
        print(f"\nStar Pluck Conquest CN: [{k_sp}] EN: '{en_data.get(k_sp)}' | CN: '{cn_data.get(k_sp)}'")

if __name__ == '__main__':
    main()
