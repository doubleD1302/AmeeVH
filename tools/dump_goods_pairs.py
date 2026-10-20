import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
data = json.load(open(ROOT / "work/batches/final_batch3_items_goods.json", encoding="utf-8"))

ag_rg = [d for d in data if d['table'] in ('ActivityGoods', 'ResidentGoods')]
unique_pairs = set((d['en'], d['zh']) for d in ag_rg)

print(f"Total AG/RG items: {len(ag_rg)}, unique pairs: {len(unique_pairs)}")
for en, zh in sorted(unique_pairs):
    print(f"  ({en!r}, {zh!r})")
