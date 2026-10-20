import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

chess_items = [d for d in data if d['key'].startswith('Item.25010')]
print(f"Total chess/badge/figurine items in batch 3: {len(chess_items)}")
for d in chess_items:
    print(f"  {d['key']}: EN={d['en']!r} | ZH={d['zh']!r}")
