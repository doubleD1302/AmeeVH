import os
import sys
import json

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")
data_en = os.path.join(viet_dir, r"work\research\data_en_original\entries")
patch_dir = r"c:\YostarGames\StellaSora_EN\Patch_Store"
pers_dir = r"c:\YostarGames\StellaSora_EN\Persistent_Store"

print(f"Checking directories...")
print(f"Decrypted entries: {len(os.listdir(data_dec)) if os.path.exists(data_dec) else 0}")
print(f"Original EN entries: {len(os.listdir(data_en)) if os.path.exists(data_en) else 0}")

if os.path.exists(patch_dir):
    print("=== Patch Store Contents ===")
    for root, dirs, files in os.walk(patch_dir):
        if files:
            rel = os.path.relpath(root, patch_dir)
            print(f"  [{rel}] {len(files)} files (e.g. {files[:3]})")

if os.path.exists(pers_dir):
    print("=== Persistent Store Contents ===")
    for d in os.listdir(pers_dir):
        p = os.path.join(pers_dir, d)
        if os.path.isdir(p):
            subfiles = os.listdir(p)
            print(f"  [{d}] {len(subfiles)} items (e.g. {subfiles[:3]})")

# Check STATUS.json and CHECKPOINT.json
status_file = os.path.join(viet_dir, "STATUS.json")
if os.path.exists(status_file):
    with open(status_file, "r", encoding="utf-8") as f:
        st = json.load(f)
    print(f"STATUS.json: {st.get('summary', {})}")
