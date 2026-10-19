import json
import os

p4_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar4_system_gacha_shops.json"
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

with open(p4_path, "r", encoding="utf-8") as f:
    p4_data = json.load(f)

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

print("Scanning Pillar 4 tables...")

# 1. Force & ContentWord
force_en = p4_data.get("Force", {}).get("entries", {})
force_cn = get_cn_dict("Force")
print(f"\nForce ({len(force_en)}):")
for k, v in force_en.items():
    print(f"  {v:35} | CN: {force_cn.get(k, '')}")

cw_en = p4_data.get("ContentWord", {}).get("entries", {})
cw_cn = get_cn_dict("ContentWord")
print(f"\nContentWord ({len(cw_en)}):")
for k, v in cw_en.items():
    print(f"  {v:35} | CN: {cw_cn.get(k, '')}")

# 2. Honor & Title
honor_en = p4_data.get("Honor", {}).get("entries", {})
honor_cn = get_cn_dict("Honor")
print(f"\nHonor (Total {len(honor_en)}):")
for k, v in list(honor_en.items())[:20]:
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {honor_cn.get(k, '')}")

title_en = p4_data.get("Title", {}).get("entries", {})
title_cn = get_cn_dict("Title")
print(f"\nTitle (Total {len(title_en)}):")
for k, v in list(title_en.items())[:20]:
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {title_cn.get(k, '')}")

# 3. Gacha & GachaType
gacha_en = p4_data.get("Gacha", {}).get("entries", {})
gacha_cn = get_cn_dict("Gacha")
print(f"\nGacha Banners ({len(gacha_en)}):")
for k, v in gacha_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {gacha_cn.get(k, '')}")

# 4. MallShop items
mall_en = p4_data.get("MallShop", {}).get("entries", {})
mall_cn = get_cn_dict("MallShop")
print(f"\nMallShop items ({len(mall_en)//2}):")
for k, v in list(mall_en.items())[:20]:
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {mall_cn.get(k, '')}")

# 5. AgentTab
agent_en = p4_data.get("AgentTab", {}).get("entries", {})
agent_cn = get_cn_dict("AgentTab")
print(f"\nAgentTab ({len(agent_en)}):")
for k, v in agent_en.items():
    if k.endswith(".1"):
        print(f"  {v:35} | CN: {agent_cn.get(k, '')}")
