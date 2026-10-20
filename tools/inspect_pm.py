import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))

pm_groups = {}
for k, v in orig.items():
    if k.startswith("PM"):
        prefix = k.split(".")[0]
        if prefix not in pm_groups:
            pm_groups[prefix] = []
        pm_groups[prefix].append((k, v, trans[k]))

print(f"Total PM Groups: {len(pm_groups)}")
for group, items in pm_groups.items():
    print(f"\nGroup {group}: {len(items)} messages")
    print(f"Sample 3 messages:")
    for k, o, t in items[:3]:
        print(f"  [{k}] EN: {o}")
        print(f"        VI: {t}")
