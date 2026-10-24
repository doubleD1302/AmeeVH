import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part1_editorial_20261025_r01")

for part_name, fname in [('A', 'PARTITION_A_SOURCE.json'), ('B', 'PARTITION_B_SOURCE.json')]:
    path = ROOT / fname
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Checking Partition {part_name}...")
    for it in data:
        ctrl = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', it['en'])
        if ctrl:
            print(f"  [{it['id']}] length={len(it['en'])} ctrl_count={len(ctrl)}: {repr(it['en'][:60])}")
