import json
import re
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00728_0xc316bcdb179b0d6e.bin', 'r', encoding='utf-8') as f:
    cn_task = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)['ActivityTask']

print(f"Total ActivityTask: {len(tasks)}")

patterns = Counter()
for it in tasks:
    en = it['en']
    # replace numbers and stage names
    p = re.sub(r'[0-9]+', '{N}', en)
    patterns[p] += 1

print(f"Unique patterns in ActivityTask: {len(patterns)}")
for p, c in patterns.most_common(25):
    print(f"  {c:3d}x: {p}")
