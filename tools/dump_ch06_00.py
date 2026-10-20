import json

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

for k in sorted(src.keys()):
    if k.startswith('STm06_00.'):
        print(f"[{k}]")
        print(f"  EN: {src[k]}")
        print(f"  VI: {dst.get(k)}")
