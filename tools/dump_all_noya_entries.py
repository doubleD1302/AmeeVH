import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

noya_entries = {}

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
    
    # Skip CN tables
    sample_text = " ".join([v for v in d.values() if isinstance(v, str)][:15])
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', sample_text))
    if cn_chars > 15:
        continue

    first_k = next(iter(d.keys()), "")
    prefix = first_k.split(".")[0] if "." in first_k else fname

    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        
        # Check if relates to Noya (ID 112)
        parts = k.split(".")
        is_noya = False
        if len(parts) > 1:
            id_part = parts[1]
            if id_part == "112" or id_part.startswith("112") or id_part.startswith("10112") or id_part.startswith("5112") or id_part.startswith("3112") or id_part.startswith("2112") or id_part.startswith("80112") or id_part.startswith("250112") or id_part.startswith("1120"):
                is_noya = True
        if "noya" in v.lower() or "firstlight" in v.lower() or "first light" in v.lower():
            is_noya = True

        if is_noya:
            if prefix not in noya_entries:
                noya_entries[prefix] = []
            noya_entries[prefix].append((fname, k, v))

print(f"Total categories with Noya entries: {len(noya_entries)}")
total_count = sum(len(v) for v in noya_entries.values())
print(f"Total Noya entries: {total_count}")

for prefix, items in sorted(noya_entries.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {prefix:30s}: {len(items):3d} entries")

# Save full dump for review
dump_path = os.path.join(viet_dir, r"work\reviews\all_noya_entries.json")
with open(dump_path, "w", encoding="utf-8") as f:
    json.dump({p: [{"file": fn, "key": k, "value": v} for fn, k, v in items] for p, items in noya_entries.items()}, f, indent=2, ensure_ascii=False)

print(f"Saved full dump to: {dump_path}")
