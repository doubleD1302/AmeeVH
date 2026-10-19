import json
from pathlib import Path

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for tname, items in data.items():
    print(f"\n=======================================================")
    print(f"TABLE: {tname} ({len(items)} items)")
    print(f"=======================================================")
    count = 0
    for it in items:
        # Show items that have actual text (not short codes like 'BT01')
        if len(it['en']) > 15:
            print(f"[{it['key']}]")
            print(f"  EN: {it['en']}")
            print(f"  VI: {it['vi_current']}")
            count += 1
            if count >= 6:
                break
