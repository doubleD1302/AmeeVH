import json
from pathlib import Path

fpath = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\audit_batch3_item_mall_task.json")
b3 = json.loads(fpath.read_text(encoding="utf-8"))

untr = [d for d in b3 if d["en"] == d["current_vi"] and d["en"] != "!NONEED!" and len(d["en"].split()) > 1]
print("Total untranslated multi-word:", len(untr))

# Save unique EN strings to examine
unique_en = {}
for d in untr:
    en = d["en"]
    if en not in unique_en:
        unique_en[en] = []
    unique_en[en].append((d["table"], d["key"]))

print(f"Total unique EN strings among untranslated: {len(unique_en)}")

# Write to a json for mapping
with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json", "w", encoding="utf-8") as out:
    json.dump([{"en": k, "occurrences": v} for k, v in unique_en.items()], out, indent=2, ensure_ascii=False)
