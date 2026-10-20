import json
from collections import defaultdict
from pathlib import Path

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

groups = defaultdict(list)
for d in data:
    k = d['key']
    t = d['table']
    if t != 'Item':
        groups[t].append(d)
        continue
    parts = k.split('.')
    item_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    if item_id == 1:
        groups['Currency_Dorra'].append(d)
    elif item_id < 100:
        groups['Basic_Resource'].append(d)
    elif 100 <= item_id < 200:
        groups['Character_Recruit'].append(d)
    elif 1000 <= item_id < 2000:
        groups['Key_Talent'].append(d)
    elif 10000 <= item_id < 20000:
        groups['Skin_Costume'].append(d)
    elif 20000 <= item_id < 40000:
        groups['Gift_Potion'].append(d)
    elif 70000 <= item_id < 90000:
        groups['Ticket_Voucher'].append(d)
    elif 110000 <= item_id < 120000:
        groups['Honor_Title'].append(d)
    elif 120000 <= item_id < 130000:
        groups['Avatar_Frame'].append(d)
    elif 130000 <= item_id < 140000:
        groups['Emoji_Sticker'].append(d)
    elif 200000 <= item_id < 300000:
        groups['Disc_Memory'].append(d)
    elif 700000 <= item_id < 800000:
        groups['Furniture'].append(d)
    elif 1000000 <= item_id < 3000000:
        groups['Chess_Badge_Figurine'].append(d)
    else:
        groups['Other'].append(d)

out = []
for gname in ['Currency_Dorra', 'Basic_Resource', 'Key_Talent', 'Skin_Costume', 'Gift_Potion', 'Disc_Memory', 'Emoji_Sticker', 'Ticket_Voucher', 'Honor_Title', 'Other', 'ActivityGoods', 'ResidentGoods']:
    items = groups[gname]
    out.append(f"==================================================")
    out.append(f"CATEGORY: {gname} ({len(items)} items)")
    out.append(f"==================================================")
    for it in items:
        out.append(f"[{it['key']}]")
        out.append(f"  EN: {it['en']}")
        out.append(f"  ZH: {it['zh']}")
    out.append("")

Path('StellaSora_VietHoa/work/batches/inspect_categories.txt').write_text('\n'.join(out), encoding='utf-8')
print("Wrote inspect_categories.txt successfully!")
