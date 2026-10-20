import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

keywords = ["firstlight", "first light", "初光", "晨光", "极光", "晨曦", "拂晓", "黎明", "first_light", "noya"]

results = []
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
        v_low = v.lower()
        k_low = k.lower()
        for kw in keywords:
            if kw in k_low or kw in v_low or kw in v:
                results.append((fname, k, v, kw))
                break

print(f"Total keyword matches: {len(results)}")
# Filter specifically for firstlight or 初光 or 晨光
fl_matches = [r for r in results if r[3] != "noya"]
print(f"Matches for 'First Light / 初光 / 晨曦...': {len(fl_matches)}")
for fname, k, v, kw in fl_matches[:30]:
    print(f"  [{k}] (matched {kw}): {v[:80]}")
