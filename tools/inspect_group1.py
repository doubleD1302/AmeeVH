import json

p = "StellaSora_VietHoa/work/batches/final_wave_group1_gameplay_minigames.json"
data = json.load(open(p, encoding="utf-8"))
print(f"Total: {len(data)}")

# Group by table
by_table = {}
for i, item in enumerate(data):
    by_table.setdefault(item["table"], []).append((i, item))

for t, items in by_table.items():
    print(f"\n=== Table: {t} ({len(items)} items) ===")
    for idx, it in items[:5]:
        print(f"  [{idx}] {it['key']}")
        print(f"       EN: {it.get('en')}")
        print(f"       ZH: {it.get('zh')}")
