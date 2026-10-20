import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))
furn_lore = [d for d in data if d['key'].startswith('Item.7') and d['key'].endswith('.3') and len(d['key'].split('.')[1]) == 6]

print(f"Total furniture lore items: {len(furn_lore)}")
for i, d in enumerate(furn_lore):
    print(f"{i:2} | {d['key']} | ZH: {d['zh']!r}")
