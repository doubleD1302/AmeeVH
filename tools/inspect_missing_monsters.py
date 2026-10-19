import json
import os

p1_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar1_dungeons_monsters.json"
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

with open(p1_path, "r", encoding="utf-8") as f:
    p1_data = json.load(f)

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

def get_cn_dict(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

mm_en = p1_data["MonsterManual"]["entries"]
mm_cn = get_cn_dict("MonsterManual")

# load current glossary
with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\config\master_glossary.json", "r", encoding="utf-8") as f:
    mg = json.load(f)
terms = mg.get("terms", {})
terms_lower = {k.lower(): v for k, v in terms.items()}

unique_monsters = {}
for k, v in mm_en.items():
    if k.endswith(".1"):
        cn_v = mm_cn.get(k, "")
        if v not in unique_monsters:
            unique_monsters[v] = cn_v

print(f"Total unique monster names in MonsterManual: {len(unique_monsters)}")
missing = {en: cn for en, cn in unique_monsters.items() if en.lower() not in terms_lower}
print(f"Missing from master glossary: {len(missing)}")

print("\nSample missing monsters (first 50):")
for en, cn in list(missing.items())[:50]:
    print(f"  EN: {en:35} | CN: {cn}")
