#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"
CN_SKILL_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00857_0xe2b9fc03308736f9.bin"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)
with open(CN_SKILL_PATH, 'r', encoding='utf-8') as f:
    cn_skill = json.load(f)

items = dataset['Skill']
unique = {}
for it in items:
    en = it['en']
    if en not in unique:
        unique[en] = {
            'key': it['key'],
            'en': en,
            'vi_current': it['vi_current'],
            'cn': cn_skill.get(it['key'], '')
        }
out_file = ROOT / 'work' / 'polish' / 'unique_skill.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(list(unique.values()), f, ensure_ascii=False, indent=2)
print(f"Skill: dumped {len(unique)} unique entries to {out_file}")
