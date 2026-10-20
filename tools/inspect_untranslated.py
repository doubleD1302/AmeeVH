import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))

untranslated = []
for k, o in orig.items():
    t = trans.get(k, "")
    if o.strip() == t.strip():
        # check if it contains ascii letters
        if re.search(r'[a-zA-Z]{3,}', o):
            untranslated.append((k, o, t))

print(f"Total untranslated identical lines: {len(untranslated)}")
for k, o, t in untranslated:
    print(f"[{k}] {repr(o)}")
