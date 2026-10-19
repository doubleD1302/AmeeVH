#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

print("=== ALL UNIQUE EN STRINGS IN SECONDARYSKILL ===")
secskill = dataset['SecondarySkill']
seen = set()
for it in secskill:
    en = it['en']
    if en not in seen:
        seen.add(en)
        if it['key'].endswith('.2'):
            print(f"[{it['key']}]")
            print(f"  EN: {en}")
            print(f"  VI: {it['vi_current']}")
