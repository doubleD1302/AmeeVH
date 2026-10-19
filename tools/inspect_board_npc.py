import json
import os

entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

# Find CN tables directly
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
                cn_tables[tbl_name] = fpath
    except Exception:
        pass

with open(cn_tables['BoardNPC'], 'r', encoding='utf-8') as f:
    cn_data = json.load(f)

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar4_system_gacha_shops.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)['BoardNPC']['entries']

seen = set()
for k, v in en_data.items():
    if v not in seen:
        seen.add(v)
        cn_v = cn_data.get(k, "")
        print(f"{v:30} | CN: {cn_v}")
