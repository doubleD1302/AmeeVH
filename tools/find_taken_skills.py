#!/usr/bin/env python3
import json

with open('StellaSora_VietHoa/work/polish/phase2a_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname in ['MainSkill', 'SecondarySkill']:
    found = 0
    for it in dataset[tname]:
        if 'taken' in it['en'].lower():
            found += 1
            if found <= 5:
                print(f"[{it['key']}]")
                print("  EN:", it['en'])
                print("  VI:", it['vi_current'])
    print(f"Total 'taken' in {tname}: {found}")
