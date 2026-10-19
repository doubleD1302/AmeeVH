import json
import os

p1_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar1_dungeons_monsters.json"
p2_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar2_voices_characters.json"
p3_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar3_story_dating_quests.json"
p4_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar4_system_gacha_shops.json"
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

def get_cn_dict(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\config\master_glossary.json", "r", encoding="utf-8") as f:
    master_glossary = json.load(f)
existing_terms = master_glossary.get("terms", {})
existing_terms_lower = {k.lower(): (k, v) for k, v in existing_terms.items()}

# Load pillars
with open(p1_path, "r", encoding="utf-8") as f: p1 = json.load(f)
with open(p2_path, "r", encoding="utf-8") as f: p2 = json.load(f)
with open(p3_path, "r", encoding="utf-8") as f: p3 = json.load(f)
with open(p4_path, "r", encoding="utf-8") as f: p4 = json.load(f)

print("Master glossary currently has:", len(existing_terms), "terms")

# Check other interesting tables in P1:
for tbl in ["WeekBossType", "WeekBossLevel", "JointDrillControl", "JointDrillLevel", "TowerDefenseItem", "StarTowerBookEntrance"]:
    if tbl in p1:
        cn_d = get_cn_dict(tbl)
        entries = p1[tbl].get("entries", {})
        print(f"\n--- P1: {tbl} ({len(entries)}) ---")
        for k, v in list(entries.items())[:10]:
            print(f"  {k} = {v[:40]} | CN: {cn_d.get(k, '')}")

# Check other interesting tables in P4:
for tbl in ["MallMonthlyCard", "ProductionType", "Production", "PenguinCardHandRank", "VampireSurvivor", "GoldenSpyItem", "OpenFunc"]:
    if tbl in p4:
        cn_d = get_cn_dict(tbl)
        entries = p4[tbl].get("entries", {})
        print(f"\n--- P4: {tbl} ({len(entries)}) ---")
        for k, v in list(entries.items())[:10]:
            print(f"  {k} = {v[:40]} | CN: {cn_d.get(k, '')}")
