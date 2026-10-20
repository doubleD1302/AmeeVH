import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00529_0xebf28ce0a9f5c404.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

for k, v in sorted(d.items()):
    if k.startswith("CharacterArchiveVoice.112"):
        print(f"  {k} -> {v}")
