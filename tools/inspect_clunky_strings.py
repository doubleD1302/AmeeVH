#!/usr/bin/env python3
"""Inspect clunky word-by-word patterns across all caches."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    cache_dir = root / 'work' / 'batches'

    clunky_patterns = [
        'sao nhổ',
        'có thể được',
        'được sử dụng',
        'được áp dụng',
        'thực hiện việc',
        'nó giải phóng',
        'bị chôn vùi',
        'chạm vào để',
        'nhấp vào',
        'được cấp',
        'được nhận',
        'tăng lên bởi',
        'giảm đi bởi',
        'gây ra bởi',
        'được kích hoạt bởi',
        'mỗi khi bạn',
        'sau khi bạn',
        'được coi là',
        'ở một mình trong',
        'những tài năng'
    ]

    caches = list(cache_dir.glob('*cache*.json')) + [cache_dir / 'uitext_translation_cache.json']
    caches = list(set([c for c in caches if c.exists()]))

    print(f"Scanning {len(caches)} cache files...")

    total_clunky = 0
    pattern_stats = {p: 0 for p in clunky_patterns}
    examples = {p: [] for p in clunky_patterns}

    for cpath in caches:
        with open(cpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            v_lower = v.lower()
            for p in clunky_patterns:
                if p in v_lower:
                    pattern_stats[p] += 1
                    total_clunky += 1
                    if len(examples[p]) < 2:
                        examples[p].append((k, v))

    print(f"\nTotal clunky/literal pattern matches: {total_clunky}")
    for p, cnt in pattern_stats.items():
        if cnt > 0:
            print(f"\nPattern '{p}': {cnt} matches")
            for k, ex in examples[p]:
                print(f"   [{k[:30]}] -> {ex[:80]}")

if __name__ == '__main__':
    main()
