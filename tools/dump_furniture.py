import json
from pathlib import Path

data = json.load(open('StellaSora_VietHoa/work/batches/final_batch3_items_goods.json', encoding='utf-8'))

furn = [d for d in data if d['key'].startswith('Item.7') and len(d['key'].split('.')[1]) == 6]
print(f"Total Furniture items: {len(furn)}")

# Group furniture items by item ID (e.g. 700003, 710001, etc.)
furn_by_id = {}
for d in furn:
    parts = d['key'].split('.')
    iid = parts[1]
    field = parts[2]
    if iid not in furn_by_id:
        furn_by_id[iid] = {}
    furn_by_id[iid][field] = d

print(f"Total unique Furniture items: {len(furn_by_id)}")

out = []
for iid, fields in sorted(furn_by_id.items()):
    name = fields.get('1', {}).get('en', 'NO_NAME')
    name_zh = fields.get('1', {}).get('zh', 'NO_ZH')
    desc = fields.get('2', {}).get('en', '')
    desc_zh = fields.get('2', {}).get('zh', '')
    lore = fields.get('3', {}).get('en', '')
    lore_zh = fields.get('3', {}).get('zh', '')
    out.append(f"ID: {iid} | Name: {name!r} ({name_zh!r})")
    if desc:
        out.append(f"   Desc: {desc!r} ({desc_zh!r})")
    if lore:
        out.append(f"   Lore: {lore!r} ({lore_zh!r})")

Path('StellaSora_VietHoa/work/batches/inspect_furniture.txt').write_text('\n'.join(out), encoding='utf-8')
print("Wrote inspect_furniture.txt successfully!")
