import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

item_map = {it['id']: it for it in items}

check_ids = [
    'CG_155_03.227', 'CG_156_01.143', 'CG_156_01.144', 'CG_156_01.146',
    'CG_156_02.200', 'CG_156_02.202', 'CG_156_03.94', 'CG_156_03.97',
    'CG_156_03.154', 'CG_156_03.185', 'CG_156_03.251', 'CG_157_02.271',
    'CG_158_02.162', 'CG_158_02.259'
]

for iid in check_ids:
    it = item_map[iid]
    print(f"[{iid}]")
    print(f"  EN: {repr(it['en'])}")
    print(f"  VI: {repr(it.get('current_vi'))}\n")
