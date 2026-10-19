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
    if not os.path.exists(fpath):
        print(f"File NOT found: {fpath}")
        continue
    
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 60)
    print(f"File: {fname}")
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Total keys: {len(data)}")
        print(f"Key sample: {list(data.keys())[:15]}")
        first_key = list(data.keys())[0]
        first_val = data[first_key]
        print(f"Sample item [{first_key}]: type={type(first_val)}")
        if isinstance(first_val, dict):
            print(f"  Keys: {list(first_val.keys())}")
            print(f"  Content: {json.dumps(first_val, ensure_ascii=False)[:300]}")
        elif isinstance(first_val, list):
            print(f"  List length: {len(first_val)}")
            if len(first_val) > 0:
                print(f"  Sample list[0]: {json.dumps(first_val[0], ensure_ascii=False)[:300]}")
    elif isinstance(data, list):
        print(f"Total items: {len(data)}")
        if len(data) > 0:
            print(f"Item 0 type: {type(data[0])}")
            print(f"Item 0: {json.dumps(data[0], ensure_ascii=False)[:300]}")
