import json
from pathlib import Path

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def inspect_table(name, n=30, min_len=0):
    items = data[name]
    print(f"\n==================== {name} ({len(items)} items) ====================")
    shown = 0
    for it in items:
        if len(it['en']) >= min_len:
            print(f"[{it['key']}]")
            print(f"  EN: {it['en']}")
            print(f"  VI: {it['vi_current']}")
            shown += 1
            if shown >= n:
                break

if __name__ == '__main__':
    inspect_table('Story', 25)
