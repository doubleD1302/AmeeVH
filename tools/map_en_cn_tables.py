import json
import os

entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

en_tables = {}
cn_tables = {}

for fname in os.listdir(entries_dir):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(entries_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and len(d) > 0:
            first_k = list(d.keys())[0]
            tbl_name = first_k.split(".")[0]
            first_v = str(list(d.values())[0])
            has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in first_v)
            if has_cn:
                cn_tables[tbl_name] = fname
            else:
                en_tables[tbl_name] = fname
    except Exception:
        pass

common = set(en_tables.keys()).intersection(set(cn_tables.keys()))
print(f"Total EN tables: {len(en_tables)}")
print(f"Total CN tables: {len(cn_tables)}")
print(f"Common tables with both EN and CN: {len(common)}")
print("Sample matched tables:")
for tbl in sorted(list(common))[:20]:
    print(f"  {tbl:30} : EN={en_tables[tbl]} | CN={cn_tables[tbl]}")
