import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

cg162 = [it for it in items if it['scene_id'].startswith('CG_162')]
with open(CAMPAIGN_DIR / "CG_162_FULL_EN.txt", "w", encoding="utf-8") as f:
    for it in cg162:
        f.write(f"[{it['id']}] ({it['scene_id']})\nEN: {it['en']}\nVI: {it.get('current_vi')}\n\n")

print(f"Dumped {len(cg162)} lines to CG_162_FULL_EN.txt")
