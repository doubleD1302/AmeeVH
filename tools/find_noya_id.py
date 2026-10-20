import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

# Search for Riona Imaizumi or character variants
print("Searching for Riona Imaizumi and Noya variants...")
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
        if "imaizumi" in v.lower() or "riona" in v.lower() or "firstlight" in v.lower() or "first light" in v.lower():
            print(f"  [{fname}] {k} -> {v}")
