import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")
data_orig = os.path.join(viet_dir, r"work\research\data_en_original\entries")
lua_tree = os.path.join(viet_dir, r"work\research\lua_tree")

print("Searching for Noya and Firstlight / First Light...")

noya_matches = []

# 1. Search in data_orig and data_dec
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
    
    for k, v in d.items():
        if not isinstance(v, str):
            continue
        # Check for Noya or Firstlight in key or value
        if "noya" in k.lower() or "noya" in v.lower() or "firstlight" in k.lower() or "firstlight" in v.lower() or "first light" in v.lower():
            noya_matches.append((fname, k, v))

print(f"Total Noya / Firstlight matches in database tables: {len(noya_matches)}")
by_prefix = {}
for fname, k, v in noya_matches:
    prefix = k.split(".")[0] if "." in k else "Other"
    by_prefix[prefix] = by_prefix.get(prefix, 0) + 1

for p, c in sorted(by_prefix.items(), key=lambda x: x[1], reverse=True):
    print(f"  {p:30s}: {c:4d} entries")

print("\nSample entries:")
for fname, k, v in noya_matches[:25]:
    print(f"  [{k}] {v[:80]}")
