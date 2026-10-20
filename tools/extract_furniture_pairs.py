import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
data = json.load(open(ROOT / "work/batches/final_batch3_items_goods.json", encoding="utf-8"))

furn = [d for d in data if d['key'].startswith('Item.7') and len(d['key'].split('.')[1]) == 6]
unique_furn_pairs = set((d['en'], d['zh']) for d in furn)

print(f"Total furniture items: {len(furn)}, unique pairs: {len(unique_furn_pairs)}")

# Categorize by field (.1, .2, .3)
names = set()
descs = set()
lores = set()

for d in furn:
    pair = (d['en'], d['zh'])
    if d['key'].endswith('.1'):
        names.add(pair)
    elif d['key'].endswith('.2'):
        descs.add(pair)
    elif d['key'].endswith('.3'):
        lores.add(pair)

print(f"Unique names: {len(names)}")
print(f"Unique descs: {len(descs)}")
print(f"Unique lores: {len(lores)}")

out = {
    "descs": sorted(list(descs)),
    "names": sorted(list(names)),
    "lores": sorted(list(lores))
}
Path(ROOT / "work/batches/furniture_pairs.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
print("Saved furniture_pairs.json!")
