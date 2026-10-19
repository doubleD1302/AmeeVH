#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

EN_CN_PAIRS = {
    'Item': ('00577_0xe60634348b826f41.bin', '00798_0xdb546f14f2f79a11.bin'),
    'Skill': ('00636_0x998f849a64309b25.bin', '00857_0xe2b9fc03308736f9.bin'),
    'MainSkill': ('00591_0x57e760255c1d3b2d.bin', '00812_0xb09952a17d27201c.bin'),
    'SecondarySkill': ('00635_0x31a8814a91313129.bin', '00856_0x439a5df5068af46c.bin'),
    'EffectDesc': ('00555_0xb5c092c120570535.bin', '00776_0x276186f7972c180f.bin')
}

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname, (en_file, cn_file) in EN_CN_PAIRS.items():
    cn_path = ROOT / "work" / "research" / "data_decrypted" / "entries" / cn_file
    with open(cn_path, 'r', encoding='utf-8') as f:
        cn_dict = json.load(f)

    items = dataset[tname]
    has_cn = sum(1 for it in items if it['key'] in cn_dict)
    print(f"Table {tname}: {len(items)} items | Matching CN keys: {has_cn}/{len(items)}")
