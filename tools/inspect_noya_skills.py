import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

categories_to_check = ["MainSkill", "SecondarySkill", "Skill", "Potential", "Talent"]

skills_found = {}

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
    
    first_k = next(iter(d.keys()), "")
    prefix = first_k.split(".")[0] if "." in first_k else ""
    if prefix in categories_to_check:
        for k, v in d.items():
            if not isinstance(v, str):
                continue
            parts = k.split(".")
            if len(parts) > 1 and (parts[1].startswith("112") or parts[1].startswith("10112") or parts[1].startswith("5112") or parts[1].startswith("3112") or parts[1].startswith("2112") or "noya" in v.lower()):
                if prefix not in skills_found:
                    skills_found[prefix] = []
                skills_found[prefix].append((fname, k, v))

print(f"Categories found: {list(skills_found.keys())}")
for cat, items in skills_found.items():
    print(f"\n=== {cat} ({len(items)} items) ===")
    for fn, k, v in items[:10]:
        print(f"  {k} -> {v}")
