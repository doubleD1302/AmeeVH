#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname, items in dataset.items():
    field_counts = Counter()
    for it in items:
        parts = it['key'].split('.')
        if len(parts) >= 2:
            field_counts[parts[-1]] += 1
    print(f"Table {tname}: {field_counts}")
