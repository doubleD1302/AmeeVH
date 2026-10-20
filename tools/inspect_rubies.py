import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))

ruby_items = []
for k, o in orig.items():
    if "<r=" in o:
        ruby_items.append((k, o, trans[k]))

print(f"Total ruby items: {len(ruby_items)}")
for k, o, t in ruby_items:
    print(f"[{k}]")
    print(f"  Orig:  {o}")
    print(f"  Trans: {t}")
