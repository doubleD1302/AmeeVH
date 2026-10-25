#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def find_all_skill_name_tables():
    # Let's check all tables in work/research/data_en_original/entries
    # or in work/polish/phase2a_dataset.json
    p = ROOT / "work" / "polish" / "phase2a_dataset.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for table, items in d.items():
            names = [it for it in items if it['key'].endswith('.1') and len(it['en']) < 60 and '\n' not in it['en']]
            if names:
                print(f"Table '{table}': {len(names)} name-like entries (ending with .1)")
                for it in names[:5]:
                    print(f"   [{it['key']}] EN='{it['en']}' | VI='{it['vi_current']}'")

if __name__ == "__main__":
    find_all_skill_name_tables()
