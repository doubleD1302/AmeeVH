import json
from pathlib import Path

fpath = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\audit_batch3_item_mall_task.json")
data = json.loads(fpath.read_text(encoding="utf-8"))

item_untr = [d for d in data if d["table"] == "Item" and d["en"] == d["current_vi"] and len(d["en"].split()) > 1 and d["en"] != "!NONEED!"]

for d in item_untr:
    print(f"{d['key']} | {d['en']}")
