import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))

# Let's inspect phone messages to check if there are any other unnatural translations
pm_items = [(k, o, trans[k]) for k, o in orig.items() if k.startswith("PM")]
print(f"Total PM items: {len(pm_items)}")

# Check for english words in PM
weird_pm = []
for k, o, t in pm_items:
    if "bạn đã cứu" in t:
        weird_pm.append((k, o, t, "bạn đã cứu"))
    if "hoa hồng" in t:
        weird_pm.append((k, o, t, "hoa hồng"))
    if "chặt chẽ" in t:
        weird_pm.append((k, o, t, "chặt chẽ"))
    if "ông chủ" in t.lower():
        weird_pm.append((k, o, t, "ông chủ"))
    if "giám đốc" in t.lower():
        weird_pm.append((k, o, t, "giám đốc"))

print(f"Weird PM items count: {len(weird_pm)}")
for item in weird_pm:
    print(f"[{item[0]}] Reason: {item[3]}")
    print(f"  EN: {item[1]}")
    print(f"  VI: {item[2]}")
