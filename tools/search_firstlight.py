import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_en = os.path.join(viet_dir, r"work\research\data_en_original\entries")
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

print("Searching for 'firstlight' or 'first light'...")
matches = []

for folder in [data_en, data_dec]:
    for fname in os.listdir(folder):
        if not fname.endswith(".bin"):
            continue
        fpath = os.path.join(folder, fname)
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
            if re.search(r'first\s*light', v, re.IGNORECASE) or re.search(r'first\s*light', k, re.IGNORECASE):
                matches.append((folder == data_en, fname, k, v))

print(f"Total matches: {len(matches)}")
seen = set()
for is_en, fname, k, v in matches:
    if k not in seen:
        seen.add(k)
        print(f"  [{k}] -> {v}")
