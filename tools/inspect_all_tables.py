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
    print(f"\n==================== {fname} ====================")
    total_entries = sum(len(tbl.get("entries", {})) for tbl in data.values())
    print(f"Total tables: {len(data)}, Total entries: {total_entries}")
    print("Tables summary:")
    for tbl_name, tbl_data in data.items():
        entries = tbl_data.get("entries", {})
        sample_keys = list(entries.keys())[:3]
        samples = [entries[k] for k in sample_keys]
        # show table name, count, sample
        sample_str = " | ".join(s.replace("\n", "\\n")[:40] for s in samples)
        print(f"  {tbl_name:30} : {len(entries):5} entries | {sample_str[:100]}")
