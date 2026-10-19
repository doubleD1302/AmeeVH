import json
import os

manifest_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"Total manifest entries: {len(manifest['entries'])}")

# Check some bin files to see if Chinese text exists in data_decrypted
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

# Let's inspect a few files from index 0 to 10 and 500 to 520 and 700 to 720
cn_files = []
en_files = []

for item in manifest['entries']:
    fname = item['filename']
    fpath = os.path.join(entries_dir, fname)
    if not os.path.exists(fpath):
        continue
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and len(d) > 0:
            first_k = list(d.keys())[0]
            first_v = str(list(d.values())[0])
            # check if first_v has chinese characters
            has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in first_v)
            if has_cn:
                cn_files.append((fname, first_k, first_v[:40]))
            else:
                en_files.append((fname, first_k, first_v[:40]))
    except Exception as e:
        pass

print(f"Total non-empty json tables: EN-like = {len(en_files)}, CN-like = {len(cn_files)}")
print("Sample CN tables:")
for f, k, v in cn_files[:10]:
    print(f"  {f} | {k} | {v}")
