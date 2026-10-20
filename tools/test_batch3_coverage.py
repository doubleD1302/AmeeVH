import json
import sys
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from batch3_dict_part1 import KEY_MAP
from batch3_dict_goods import GOODS_MAP
from batch3_dict_furniture_descs import FURN_DESCS
from batch3_dict_furniture_names import FURN_NAMES
from batch3_dict_furniture_lores import FURN_LORES

data = json.load(open(ROOT / "work/batches/final_batch3_items_goods.json", encoding="utf-8"))
print(f"Total items in batch 3: {len(data)}")

unmapped = []
for d in data:
    k = d["key"]
    en = d["en"]
    zh = d["zh"]
    pair = (en, zh)
    
    trans = None
    if k in KEY_MAP:
        trans = KEY_MAP[k]
    elif pair in GOODS_MAP:
        trans = GOODS_MAP[pair]
    elif pair in FURN_DESCS:
        trans = FURN_DESCS[pair]
    elif pair in FURN_NAMES:
        trans = FURN_NAMES[pair]
    elif pair in FURN_LORES:
        trans = FURN_LORES[pair]
        
    if not trans:
        unmapped.append(d)

print(f"Unmapped items: {len(unmapped)}")
if unmapped:
    print("Sample unmapped:")
    for u in unmapped[:15]:
        print(f"  [{u['key']}] EN: {u['en']!r} | ZH: {u['zh']!r}")
else:
    print("SUCCESS: 100% OF 816 ITEMS ARE COVERED!")
