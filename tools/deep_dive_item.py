#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

items = dataset['Item']

# Let's inspect items where EN has words like:
# "used in", "can be", "latent", "unseals", "currency", "circulate", "scrap paper", "Monolith", "Star Pluck", "ticket", "disc", "gacha"
keywords = [
    "currency", "Monolith", "Star Pluck", "ticket", "disc", "soul key", "unseal", "latent",
    "buried", "talent", "used for", "can be used", "scrap paper", "circulate", "Deepsea",
    "tier-up", "crescendo", "gacha", "summon", "recruit", "grant", "exchange"
]

print("=== ITEM TABLE DEEP DIVE ===")
for kw in keywords:
    matches = [it for it in items if kw in it['en'].lower()]
    print(f"\nKeyword '{kw}': {len(matches)} matches")
    for m in matches[:3]:
        print(f"  Key: {m['key']}")
        print(f"    EN: {m['en']}")
        print(f"    VI: {m['vi_current']}")
