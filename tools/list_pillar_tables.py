import json
import os

files = [
    "pillar1_dungeons_monsters.json",
    "pillar2_voices_characters.json",
    "pillar3_story_dating_quests.json",
    "pillar4_system_gacha_shops.json"
]

base_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches"

for fname in files:
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n==================== {fname} ({len(data)} tables) ====================")
    tables = sorted([(k, len(v.get("entries", {}))) for k, v in data.items()], key=lambda x: x[1], reverse=True)
    for name, cnt in tables:
        print(f"  {name:32} : {cnt:5} entries")
