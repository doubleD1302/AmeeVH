import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

char_recruits = [d for d in data if d['key'].startswith('Item.1') and len(d['key'].split('.')[1]) == 3]
print(f"Total Character_Recruit: {len(char_recruits)}")
for d in char_recruits:
    print(f"  {d['key']}: EN={d['en']!r} | ZH={d['zh']!r}")
