#!/usr/bin/env python3
"""Check token consistency in current phase1_dataset.json."""

import json
from pathlib import Path
from token_validator import extract_tokens

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for tbl, items in data.items():
        mismatches = []
        for it in items:
            k = it['key']
            en_tokens = extract_tokens(it['en'])
            vi_tokens = extract_tokens(it['vi_current'])
            if en_tokens != vi_tokens:
                mismatches.append((k, it['en'], it['vi_current'], en_tokens, vi_tokens))

        print(f"{tbl}: {len(mismatches)} / {len(items)} token mismatches currently.")
        for k, en, vi, et, vt in mismatches[:5]:
            print(f"  [{k}]")
            print(f"     EN: {en}")
            print(f"     VI: {vi}")
            print(f"     EN tokens: {et}")
            print(f"     VI tokens: {vt}")

if __name__ == '__main__':
    main()
