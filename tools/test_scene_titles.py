import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

# Look at lines indexed .1, .2, .3, .4, .5, .6
for k, v in src.items():
    idx = int(k.split('.')[-1])
    if idx <= 5 and len(v.split()) <= 6 and not v.startswith('avg') and not any(ord(c) < 32 for c in v):
        print(f"{k:15}: EN='{v}' -> VI='{dst.get(k)}'")
