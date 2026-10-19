import json
from pathlib import Path

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for tname in ['Story', 'ActivityStory', 'ActivityGoods', 'PenguinCard', 'ActivityTask']:
    items = data[tname]
    same = [it for it in items if it['en'] == it['vi_current']]
    print(f"\n=== Table {tname}: {len(same)} identical to EN ===")
    for it in same[:20]:
        print(f"  [{it['key']}] -> '{it['en']}'")
