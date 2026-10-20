import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00527_0x843b3b0812018dd2.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

noya_content = {k: v for k, v in d.items() if k.startswith("CharacterArchiveContent.112")}
print(f"Total CharacterArchiveContent entries for Noya: {len(noya_content)}")
for k, v in sorted(noya_content.items()):
    print(f"\n[{k}]")
    print(v[:150] + ("..." if len(v) > 150 else ""))
