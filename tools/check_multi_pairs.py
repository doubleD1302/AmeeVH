import json
from collections import defaultdict

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

pair_map = defaultdict(list)
for d in data:
    pair_map[(d['en'], d['zh'])].append(d)

multi_pairs = {k: v for k, v in pair_map.items() if len(v) > 1}
print(f"Total multi-occurrence pairs: {len(multi_pairs)}")

for (en, zh), items in sorted(multi_pairs.items(), key=lambda x: -len(x[1])):
    keys = [it['key'] for it in items]
    tables = set(it['table'] for it in items)
    if len(tables) > 1 or any(k.startswith('Item.10') for k in keys) or any(k.startswith('Item.2501') for k in keys):
        print(f"EN: {en!r} | ZH: {zh!r} | Count: {len(items)} | Tables: {tables} | Keys sample: {keys[:5]}")
