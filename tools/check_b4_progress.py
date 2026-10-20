import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
cache_path = os.path.join(viet_dir, r"work\batches\pillars_translation_cache.json")
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

print(f"Total keys in global cache: {len(cache):,}")

for part in ["partA", "partB", "partC"]:
    path = os.path.join(viet_dir, f"work\\batches\\batch_10k_b4_{part}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    unique_vals = list(set(data.values()))
    resolved = sum(1 for v in unique_vals if v in cache)
    print(f"{part}: {resolved:,} / {len(unique_vals):,} unique strings resolved ({(resolved/len(unique_vals))*100:.1f}%) | Total strings: {len(data):,}")
