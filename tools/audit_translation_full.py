#!/usr/bin/env python3
"""Audit the entire translation for untranslated tables and clunky mechanics."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    orig_dir = root / 'work' / 'research' / 'data_en_original' / 'entries'

    clunky_patterns = [
        'điểm "',
        'tối đa 3 điểm',
        'tối đa 5 điểm',
        'tối đa 10 điểm',
        'tối đa 4 điểm',
        'với "',
        'bởi <color',
        'gánh chịu của mục tiêu bởi',
        'gánh chịu bởi',
        'bởi 1',
        'bởi 2',
        'bởi 5'
    ]

    pattern_matches = {p: [] for p in clunky_patterns}
    tables_summary = []

    for f in sorted(entries_dir.glob('*.bin')):
        with open(f, 'r', encoding='utf-8') as fp:
            try:
                curr = json.load(fp)
            except Exception:
                continue
        if not isinstance(curr, dict) or not curr:
            continue

        orig_f = orig_dir / f.name
        if not orig_f.exists():
            continue
        try:
            orig = json.load(open(orig_f, 'r', encoding='utf-8'))
        except Exception:
            continue

        changed = sum(1 for k, v in curr.items() if v != orig.get(k))
        if changed > 0:
            tables_summary.append((f.name, changed, len(curr)))

        for k, v in curr.items():
            if isinstance(v, str):
                for p in clunky_patterns:
                    if p in v:
                        pattern_matches[p].append((f.name, k, v))

    print(f"Total active translated tables: {len(tables_summary)}")
    total_translated_strings = sum(t[1] for t in tables_summary)
    print(f"Total translated strings in these tables: {total_translated_strings}")

    print("\n--- Summary of Clunky Skill Mechanics Patterns ---")
    for p, matches in pattern_matches.items():
        print(f"  Pattern '{p}': {len(matches)} occurrences")
        if matches:
            ex = matches[0]
            print(f"    Sample: [{ex[0]} - {ex[1]}]: {ex[2][:90]}...")

    # Also inspect Disc tables specifically
    disc_ip_f = '00553_0x1f924138769d46ec.bin'
    disc_tag_f = '00554_0x3abeeca79d3ed963.bin'
    print("\n--- Disc Tables Status ---")
    for df in [disc_ip_f, disc_tag_f]:
        with open(entries_dir / df, 'r', encoding='utf-8') as fp:
            d = json.load(fp)
        with open(orig_dir / df, 'r', encoding='utf-8') as ofp:
            od = json.load(ofp)
        c = sum(1 for k, v in d.items() if v != od.get(k))
        print(f"  {df}: {c}/{len(d)} translated ({(c/len(d))*100:.1f}%)")

if __name__ == '__main__':
    main()
