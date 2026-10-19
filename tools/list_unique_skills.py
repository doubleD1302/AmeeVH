#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

print("=== SAMPLE UNIQUE EN STRINGS IN SKILL ===")
skills = dataset['Skill']
seen = set()
for it in skills:
    en = it['en']
    if en not in seen:
        seen.add(en)
        if it['key'].endswith('.2') or it['key'].endswith('.13'):
            if len(seen) % 20 == 0:
                print(f"[{it['key']}]")
                print(f"  EN: {en}")
                print(f"  VI: {it['vi_current']}")
