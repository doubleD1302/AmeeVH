import os
import json
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")
data_en = os.path.join(viet_dir, r"work\research\data_en_original\entries")
ckpt_file = os.path.join(viet_dir, "CHECKPOINT.json")

with open(ckpt_file, "r", encoding="utf-8") as f:
    ckpt = json.load(f)
completed_ids = set(ckpt.get("completed_translation_ids", []))

all_tables = [f[:-5] for f in os.listdir(data_dec) if f.endswith(".json")]
print(f"Total tables in data_dec: {len(all_tables)}")
print(f"Completed table IDs in checkpoint: {len(completed_ids)}")

def extract_strings(obj):
    texts = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            texts.extend(extract_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(extract_strings(item))
    elif isinstance(obj, str):
        s = obj.strip()
        if len(s) > 1 and re.search(r'[a-zA-Z]{2,}', s) and not s.startswith("http") and not (s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Audio/") or s.startswith("Prefabs/")):
            texts.append(s)
    return texts

untranslated_tables = []
for t in all_tables:
    if t in completed_ids:
        continue
    fpath = os.path.join(data_dec, f"{t}.json")
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        strs = extract_strings(data)
        if strs:
            untranslated_tables.append((t, len(strs), len(data) if isinstance(data, list) else 1))
    except Exception as e:
        pass

untranslated_tables.sort(key=lambda x: x[1], reverse=True)
print(f"Untranslated tables with text: {len(untranslated_tables)}")
print(f"Total untranslated string occurrences: {sum(x[1] for x in untranslated_tables)}")

print("\nTop 50 untranslated tables by string count:")
for t, s_cnt, rows in untranslated_tables[:50]:
    print(f"  {t:40s} | {s_cnt:6d} strings | {rows:5d} rows")
