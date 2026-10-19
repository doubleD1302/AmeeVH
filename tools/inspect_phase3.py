import json
from pathlib import Path

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total tables: {len(data)}")
for table_name, items in data.items():
    same_as_en = sum(1 for x in items if x['en'] == x['vi_current'])
    diff = len(items) - same_as_en
    print(f"\nTable: {table_name} (Total: {len(items)}, Translated: {diff}, Same as EN: {same_as_en})")
    print("Samples:")
    for i, item in enumerate(items[:5]):
        en = item['en'].replace('\n', '\\n')[:80]
        vi = item['vi_current'].replace('\n', '\\n')[:80]
        print(f"  [{i}] key={item['key']}")
        print(f"      EN: {en}")
        print(f"      VI: {vi}")
