import json
from verify_classification import classify

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))
for d in data:
    c = classify(d)
    if c in ('Other', 'GachaTickets'):
        print(f"{c:12} | {d['key']:15} | EN: {d['en'][:30]:30} | ZH: {d['zh']}")
