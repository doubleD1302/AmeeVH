import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

for fname in os.listdir(data_dec):
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
    if any(k.startswith("Character.") for k in d.keys()):
        for k, v in sorted(d.items()):
            if k.endswith(".1"):
                print(f"  {k} -> {v}")
