import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

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
    
    dating_noya = {k: v for k, v in d.items() if (k.startswith("DatingCharacterEvent.112") or k.startswith("DatingStartEndEvent.112"))}
    if dating_noya:
        print(f"=== {fname} ({len(dating_noya)} items) ===")
        for k, v in sorted(dating_noya.items()):
            print(f"[{k}] {v}")
