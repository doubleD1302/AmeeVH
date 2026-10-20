import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00527_0x843b3b0812018dd2.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

for k, v in sorted(d.items()):
    if k.startswith("CharacterArchiveContent.112"):
        print("=" * 60)
        print(f"[{k}]")
        print(v)
