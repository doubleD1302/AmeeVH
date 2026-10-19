#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"
CN_MAIN_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00812_0xb09952a17d27201c.bin"
CN_SEC_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00856_0x439a5df5068af46c.bin"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)
with open(CN_MAIN_PATH, 'r', encoding='utf-8') as f:
    cn_main = json.load(f)
with open(CN_SEC_PATH, 'r', encoding='utf-8') as f:
    cn_sec = json.load(f)

# Save unique pairs for inspection
def dump_unique(table_name, cn_dict, out_file):
    items = dataset[table_name]
    unique = {}
    for it in items:
        en = it['en']
        if en not in unique:
            unique[en] = {
                'key': it['key'],
                'en': en,
                'vi_current': it['vi_current'],
                'cn': cn_dict.get(it['key'], '')
            }
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique.values()), f, ensure_ascii=False, indent=2)
    print(f"{table_name}: dumped {len(unique)} unique entries to {out_file}")

dump_unique('MainSkill', cn_main, ROOT / 'work' / 'polish' / 'unique_mainskill.json')
dump_unique('SecondarySkill', cn_sec, ROOT / 'work' / 'polish' / 'unique_secskill.json')
