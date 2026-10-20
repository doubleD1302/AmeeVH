import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

for f in sorted(os.listdir(data_dec)):
    if not f.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, f)
    with open(fpath, "r", encoding="utf-8") as fp:
        try:
            d = json.load(fp)
            if isinstance(d, dict) and any(k.startswith("Talent.") for k in list(d.keys())[:5]):
                sample = list(d.items())[:3]
                print(f"File {f}: {len(d)} keys. Sample: {sample}")
        except Exception:
            pass
