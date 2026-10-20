import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))
furn_names = [d for d in data if d['key'].startswith('Item.7') and d['key'].endswith('.1') and len(d['key'].split('.')[1]) == 6]

print(f"Total furniture names: {len(furn_names)}")
for i, d in enumerate(furn_names):
    print(f"{i:3} | {d['key']} | EN: {d['en']:30} | ZH: {d['zh']}")
