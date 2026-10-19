import json
import os

entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

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

p1_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar1_dungeons_monsters.json"
p4_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar4_system_gacha_shops.json"

with open(p1_path, "r", encoding="utf-8") as f:
    p1_data = json.load(f)
with open(p4_path, "r", encoding="utf-8") as f:
    p4_data = json.load(f)

def scan_table_names(data, tbl_name, name_field="1"):
    entries = data.get(tbl_name, {}).get("entries", {})
    cn_data = {}
    if tbl_name in cn_tables:
        with open(cn_tables[tbl_name], "r", encoding="utf-8") as f:
            cn_data = json.load(f)
    results = {}
    for k, v in entries.items():
        if k.endswith(f".{name_field}"):
            cn_v = cn_data.get(k, "")
            results[v] = cn_v
    return results

# 1. TravelerDuelChallengeAffix
tdca = scan_table_names(p1_data, "TravelerDuelChallengeAffix", "1")
print(f"TravelerDuelChallengeAffix: {len(tdca)} unique skill/affix names")
for en, cn in list(tdca.items())[:20]:
    print(f"  {en:35} | CN: {cn}")

# 2. RegionBossAffix
rba = scan_table_names(p1_data, "RegionBossAffix", "1")
print(f"\nRegionBossAffix: {len(rba)} unique boss skills")
for en, cn in list(rba.items())[:20]:
    print(f"  {en:35} | CN: {cn}")

# 3. SoldierPotential
sp = scan_table_names(p1_data, "SoldierPotential", "1")
print(f"\nSoldierPotential: {len(sp)} unique potential names")
for en, cn in list(sp.items())[:20]:
    print(f"  {en:35} | CN: {cn}")

# 4. TowerDefensePotential
tdp = scan_table_names(p1_data, "TowerDefensePotential", "1")
print(f"\nTowerDefensePotential: {len(tdp)} unique TD potentials")
for en, cn in list(tdp.items())[:20]:
    print(f"  {en:35} | CN: {cn}")

# 5. SubNoteSkill
sns = scan_table_names(p4_data, "SubNoteSkill", "1")
print(f"\nSubNoteSkill: {len(sns)} unique disc skills")
for en, cn in list(sns.items())[:20]:
    print(f"  {en:35} | CN: {cn}")

# 6. VampireTalent
vt = scan_table_names(p4_data, "VampireTalent", "1")
print(f"\nVampireTalent: {len(vt)} unique vampire talents")
for en, cn in list(vt.items())[:20]:
    print(f"  {en:35} | CN: {cn}")
