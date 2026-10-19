import json
import re
from pathlib import Path

with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)['ActivityTask']

clear_stages = set()
for it in tasks:
    en = it['en']
    m = re.match(r'Clear (.+?)(?: with 3★|\.|$)', en)
    if m:
        stg = m.group(1).strip()
        if 'Battle Stages' not in stg:
            clear_stages.add(stg)

print(f"Clear stages found: {len(clear_stages)}")
for s in sorted(clear_stages):
    print("  -", s)
