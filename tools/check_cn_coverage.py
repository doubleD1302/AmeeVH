#!/usr/bin/env python3
"""Check CN coverage across tables and find where CN sources are."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    with open(ds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for table, items in data.items():
        with_cn = sum(1 for it in items if it.get('cn'))
        print(f"{table}: {with_cn}/{len(items)} have CN references ({with_cn*100//len(items)}%)")

    # Check if there are other CN files in work/
    print("\nSearching for other CN files in work/...")
    work = root / 'work'
    for p in work.rglob('*.json'):
        if any(w in p.name.lower() for w in ['cn', 'zh', 'chinese', 'bilingual', 'original']):
            print(f"  Found: {p.relative_to(root)} ({p.stat().st_size} bytes)")

if __name__ == '__main__':
    main()
