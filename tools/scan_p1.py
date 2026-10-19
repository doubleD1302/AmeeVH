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

print("Scanning Pillar 1 tables...")

# 1. MonsterManual
mm_en = p1_data["MonsterManual"]["entries"]
mm_cn = get_cn_dict("MonsterManual")

monster_names = {}
for k, v in mm_en.items():
    if k.endswith(".1"): # Name field
        cn_v = mm_cn.get(k, "")
        monster_names[v] = {"cn": cn_v, "key": k}

print(f"Total unique MonsterManual names: {len(monster_names)}")
for en, info in list(monster_names.items())[:35]:
    print(f"  {en:35} | CN: {info['cn']:25} | Key: {info['key']}")

# 2. RegionBoss & RegionBossAffix
rb_en = p1_data.get("RegionBoss", {}).get("entries", {})
rb_cn = get_cn_dict("RegionBoss")
print(f"\nRegionBoss (Total {len(rb_en)}):")
for k, v in rb_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {rb_cn.get(k, '')}")

rba_en = p1_data.get("RegionBossAffix", {}).get("entries", {})
rba_cn = get_cn_dict("RegionBossAffix")
print(f"\nRegionBossAffix (Total {len(rba_en)}):")
for k, v in list(rba_en.items())[:20]:
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {rba_cn.get(k, '')}")

# 3. TravelerDuelBoss & TravelerDuelChallengeAffix
tdb_en = p1_data.get("TravelerDuelBoss", {}).get("entries", {})
tdb_cn = get_cn_dict("TravelerDuelBoss")
print(f"\nTravelerDuelBoss:")
for k, v in tdb_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {tdb_cn.get(k, '')}")

# 4. InfinityTower & StarTowerGroup
it_en = p1_data.get("InfinityTower", {}).get("entries", {})
it_cn = get_cn_dict("InfinityTower")
print(f"\nInfinityTower:")
for k, v in it_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {it_cn.get(k, '')}")

stg_en = p1_data.get("StarTowerGroup", {}).get("entries", {})
stg_cn = get_cn_dict("StarTowerGroup")
print(f"\nStarTowerGroup:")
for k, v in stg_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {stg_cn.get(k, '')}")
