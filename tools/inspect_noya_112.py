import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")
data_orig = os.path.join(viet_dir, r"work\research\data_en_original\entries")

# Character ID 112 is Noya!
# Let's inspect all entries related to 112
print("Inspecting everything for Character 112 (Noya)...")

noya_tables = {}

for fname in sorted(os.listdir(data_dec)):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        try:
            d = json.load(f)
        except Exception:
            continue
    if not isinstance(d, dict):
        continue
    
    # Check if this is CN table
    sample_text = " ".join([v for v in d.values() if isinstance(v, str)][:15])
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', sample_text))
    if cn_chars > 15:
        continue
    
    prefix = next(iter(d.keys())).split(".")[0] if "." in next(iter(d.keys())) else fname
    
    matches = {}
    for k, v in d.items():
        if not isinstance(v, str):
            continue
        # Check if key is related to 112 or contains 112
        parts = k.split(".")
        has_112 = False
        if len(parts) > 1:
            # Check ID part
            id_part = parts[1]
            if id_part == "112" or id_part.startswith("112") or id_part.startswith("10112") or id_part.startswith("5112") or id_part.startswith("3112") or id_part.startswith("2112") or id_part.startswith("80112") or id_part.startswith("250112") or id_part.startswith("1120"):
                has_112 = True
        if has_112 or "noya" in v.lower() or "firstlight" in v.lower() or "first light" in v.lower():
            matches[k] = v

    if matches:
        noya_tables[prefix] = matches

print(f"Tables with Noya (112) data: {len(noya_tables)}")
for p, m in sorted(noya_tables.items()):
    print(f"\n=== {p} ({len(m)} items) ===")
    for k, v in list(m.items())[:8]:
        print(f"  {k}: {v[:100]}")
