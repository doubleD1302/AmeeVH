import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

for d in data:
    for name in ['Amber', 'Iris', 'Tilia', 'Kasimira', 'Firenze', 'Noya']:
        if d['en'] == name:
            print(f"{d['key']}: EN={d['en']!r} | ZH={d['zh']!r}")
