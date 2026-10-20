import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
data = json.load(open(ROOT / "work/batches/final_batch3_items_goods.json", encoding="utf-8"))

def classify(d):
    k = d['key']
    t = d['table']
    if t == 'ActivityGoods':
        return 'AG'
    if t == 'ResidentGoods':
        return 'RG'
    parts = k.split('.')
    iid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    fld = parts[2] if len(parts) > 2 else ''
    
    if iid == 1:
        return 'Currency'
    if iid < 100:
        return 'BasicResource'
    if 100 <= iid < 200:
        return 'CharShard'
    if 1000 <= iid < 2000:
        return 'KeyTalent'
    if 10000 <= iid < 20000:
        return 'SkinCostume'
    if 20000 <= iid < 40000:
        return 'GiftPotion'
    if 70000 <= iid < 90000:
        return 'TicketVoucher'
    if 110000 <= iid < 120000:
        return 'HonorTitle'
    if 130000 <= iid < 140000:
        return 'Avatar'
    if 200000 <= iid < 300000:
        return 'DiscMemory'
    if 500000 <= iid < 600000:
        return 'RunesAffixes'
    if 600 <= iid < 800:
        return 'GachaTickets'
    if 700000 <= iid < 800000:
        return 'Furniture'
    if 1000000 <= iid < 3000000:
        return 'ChessUnit'
    return 'Other'

from collections import defaultdict
grouped = defaultdict(list)
for d in data:
    c = classify(d)
    grouped[c].append(d)

for c, items in sorted(grouped.items()):
    unique_pairs = set((it['en'], it['zh']) for it in items)
    print(f"{c:15}: {len(items):3} items | {len(unique_pairs):3} unique pairs")
