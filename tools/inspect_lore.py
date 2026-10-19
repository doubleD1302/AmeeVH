#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00577_0xe60634348b826f41.bin"
CN_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00798_0xdb546f14f2f79a11.bin"

with open(EN_PATH, 'r', encoding='utf-8') as f:
    en_data = json.load(f)
with open(CN_PATH, 'r', encoding='utf-8') as f:
    cn_data = json.load(f)

# Look at items with .3 ending (lore descriptions)
lore_keys = [k for k in en_data.keys() if k.endswith('.3')]
print(f"Total lore keys (.3) in Item: {len(lore_keys)}")

for k in lore_keys[:20]:
    print(f"Key: {k}")
    print(f"  EN: {en_data[k]}")
    print(f"  CN: {cn_data.get(k, '')}")
