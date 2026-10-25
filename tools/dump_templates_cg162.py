import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for s_id in ['CG_162_01', 'CG_162_02', 'CG_162_03']:
    s_items = [it for it in items if it['scene_id'] == s_id]
    out_file = ROOT / f"tools/template_{s_id}.py"
    with open(out_file, "w", encoding="utf-8") as out:
        out.write(f"# -*- coding: utf-8 -*-\nTRANSLATIONS_{s_id} = {{\n")
        for it in s_items:
            out.write(f"    {repr(it['id'])}: {repr(it['en'])},\n")
        out.write("}\n")
    print(f"Wrote {len(s_items)} lines to template_{s_id}.py")
