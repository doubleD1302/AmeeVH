import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

scenes = sorted(list(set(it['scene_id'] for it in items)))
for s in scenes:
    s_items = [it for it in items if it['scene_id'] == s]
    # Look at first 5 lines
    print(f"=== {s} ===")
    for it in s_items[:4]:
        print(f"  {it['id']}: EN: {it['en']}")
        print(f"           VI: {it.get('current_vi')}")
    print()
