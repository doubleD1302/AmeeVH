import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00528_0xd8b61831cfe58bf2.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

noya_voices = {k: v for k, v in d.items() if k.startswith("CharacterArchiveVoice.112")}
print(f"Total Noya voice lines: {len(noya_voices)}")
for k, v in list(noya_voices.items())[:25]:
    print(f"  {k} -> {v}")
