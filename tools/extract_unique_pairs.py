import json
from collections import defaultdict
from pathlib import Path

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

# Group all occurrences by (en, zh)
pair_map = defaultdict(list)
for d in data:
    pair_map[(d['en'], d['zh'])].append(d)

print(f"Total unique (en, zh) pairs: {len(pair_map)}")

pairs_list = []
for (en, zh), items in sorted(pair_map.items(), key=lambda x: (x[1][0]['table'], x[1][0]['key'])):
    pairs_list.append({
        "sample_key": items[0]['key'],
        "table": items[0]['table'],
        "count": len(items),
        "en": en,
        "zh": zh,
        "all_keys": [it['key'] for it in items]
    })

Path('StellaSora_VietHoa/work/batches/unique_pairs_batch3.json').write_text(
    json.dumps(pairs_list, indent=2, ensure_ascii=False),
    encoding='utf-8'
)
print("Wrote unique_pairs_batch3.json successfully!")
