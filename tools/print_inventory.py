import json

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\text_inventory_summary.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total categories: {len(items)}")
for item in items[:50]:
    cat = item["category"]
    cnt = item["count"]
    fc = item["files_count"]
    ek = item["example_key"]
    et = item["example_text"].replace("\n", " ")
    print(f"{cat:35s} | count: {cnt:6d} | files: {fc:2d} | ex: {ek[:30]} -> {et[:40]}")
