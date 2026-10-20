import json
from pathlib import Path

fpath = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\audit_batch3_item_mall_task.json")
data = json.loads(fpath.read_text(encoding="utf-8"))

item_untr = [d for d in data if d["table"] == "Item" and d["en"] == d["current_vi"] and len(d["en"].split()) > 1 and d["en"] != "!NONEED!"]

dorm = [d for d in item_untr if any(d["key"].startswith(p) for p in ["Item.70", "Item.71", "Item.72", "Item.73", "Item.74"])]
non_dorm = [d for d in item_untr if d not in dorm]

print(f"Dorm items count: {len(dorm)}")
print(f"Non-dorm items count: {len(non_dorm)}")

print("\n--- Non-dorm sample (first 25) ---")
for d in non_dorm[:25]:
    print(f"[{d['key']}] {d['en']}")

if len(non_dorm) > 25:
    print(f"\n--- Non-dorm remaining ({len(non_dorm)-25}) ---")
    for d in non_dorm[25:]:
        print(f"[{d['key']}] {d['en']}")
