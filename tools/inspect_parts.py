import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
for part in ["partA", "partB", "partC"]:
    path = os.path.join(viet_dir, f"work\\batches\\batch_10k_b4_{part}_translated.json")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"{part}: {len(d)} items")
    # inspect first 3 items:
    sample_keys = list(d.keys())[:5]
    for k in sample_keys:
        print(f"  {k} -> {d[k]}")
