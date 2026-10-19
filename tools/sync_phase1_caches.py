#!/usr/bin/env python3
"""Sync polished phase 1 translations into batch caches."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    pol_path = root / 'work' / 'polish' / 'phase1_polished.json'
    uitext_cache_path = root / 'work' / 'batches' / 'uitext_translation_cache.json'
    sys_cache_path = root / 'work' / 'batches' / 'system_tables_translation_cache.json'

    with open(pol_path, 'r', encoding='utf-8') as f:
        polished = json.load(f)

    # 1. Update uitext cache
    if uitext_cache_path.exists():
        with open(uitext_cache_path, 'r', encoding='utf-8') as f:
            ui_cache = json.load(f)
        for k, v in polished['UIText'].items():
            ui_cache[k] = v
        with open(uitext_cache_path, 'w', encoding='utf-8') as f:
            json.dump(ui_cache, f, ensure_ascii=False, indent=2)
        print(f"Updated {uitext_cache_path.name}: {len(polished['UIText'])} entries synced.")

    # 2. Update system tables cache
    if sys_cache_path.exists():
        with open(sys_cache_path, 'r', encoding='utf-8') as f:
            sys_cache = json.load(f)
        for tbl in ['Word', 'DictionaryDiagram', 'MailTemplate']:
            for k, v in polished[tbl].items():
                sys_cache[k] = v
        with open(sys_cache_path, 'w', encoding='utf-8') as f:
            json.dump(sys_cache, f, ensure_ascii=False, indent=2)
        print(f"Updated {sys_cache_path.name}: Word, Dict, Mail entries synced.")

if __name__ == '__main__':
    main()
