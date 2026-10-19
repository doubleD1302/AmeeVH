#!/usr/bin/env python3
"""List all 19 token mismatches in UIText."""

import json
from pathlib import Path
from token_validator import extract_tokens

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    uitext = data['UIText']
    mismatches = []
    for it in uitext:
        k = it['key']
        en_tokens = extract_tokens(it['en'])
        vi_tokens = extract_tokens(it['vi_current'])
        if en_tokens != vi_tokens:
            mismatches.append((k, it['en'], it['vi_current'], en_tokens, vi_tokens))

    print(f"Total UIText token mismatches: {len(mismatches)}")
    for k, en, vi, et, vt in mismatches:
        print(f"\n[{k}]")
        print(f"  EN: {repr(en)}")
        print(f"  VI: {repr(vi)}")
        print(f"  EN Tokens: {et}")
        print(f"  VI Tokens: {vt}")

if __name__ == '__main__':
    main()
