#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import load_master_glossary, load_cache
from run_translator_pillar2 import build_domain_lookup

terms, forbidden = load_master_glossary()
cache = load_cache()

with open("work/batches/pillar2_voices_characters.json", "r", encoding="utf-8") as f:
    p2_data = json.load(f)

lookup = build_domain_lookup(terms, p2_data)

to_translate = []
for tbl_name, tbl_info in p2_data.items():
    for k, v in tbl_info.get("entries", {}).items():
        if not v or not v.strip():
            continue
        if v in lookup or v.lower() in lookup or v in cache:
            continue
        to_translate.append(v)

unique = list(dict.fromkeys(to_translate))
total_count = sum(v["count"] for v in p2_data.values())
print(f"P2 Total: {total_count}, Unique remaining to translate: {len(unique)}")
if unique:
    print("Sample 5:", unique[:5])
