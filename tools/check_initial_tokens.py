#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

TOKEN_REGEX = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|&Param\d+&|##[^#]+(?:#[^#]+)?#|#\d+#)')

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname, items in dataset.items():
    mismatches = 0
    for it in items:
        en_tokens = TOKEN_REGEX.findall(it['en'])
        vi_tokens = TOKEN_REGEX.findall(it['vi_current'])
        if sorted(en_tokens) != sorted(vi_tokens):
            mismatches += 1
            if mismatches <= 3:
                print(f"Mismatch in {tname} [{it['key']}]:")
                print(f"  EN: {it['en']}")
                print(f"  VI: {it['vi_current']}")
                print(f"  EN toks: {en_tokens}")
                print(f"  VI toks: {vi_tokens}")
    print(f"Table {tname}: {mismatches} / {len(items)} token mismatches in current data")
