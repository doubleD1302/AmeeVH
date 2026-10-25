import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

unclosed_ids = [
    'CG_155_03.96', 'CG_155_03.126', 'CG_157_01.79', 'CG_157_01.83', 'CG_157_01.232',
    'CG_157_02.170', 'CG_158_01.45', 'CG_158_01.294', 'CG_158_02.162', 'CG_158_02.277',
    'CG_158_03.128'
]

item_map = {it['id']: it for it in items}
for iid in unclosed_ids:
    it = item_map.get(iid)
    if it:
        print(f"[{iid}] EN: {repr(it['en'])}")
        print(f"       VI: {repr(it.get('current_vi'))}\n")
    else:
        print(f"[{iid}] NOT FOUND!\n")
