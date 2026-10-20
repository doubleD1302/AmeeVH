import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

for k, v in src.items():
    if re.match(r'^Act\s+[A-Za-z]+$', v.strip()):
        print(f'{k:15}: EN="{v}" -> VI="{dst.get(k)}"')
