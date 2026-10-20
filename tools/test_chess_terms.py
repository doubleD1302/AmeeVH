import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

# Search for chess terms: pawn, bishop, rook, knight, queen, king, piece
for k, v in src.items():
    if re.search(r'\b(pawn|bishop|rook|knight|queen|king)\b', v, re.I):
        print(f"[{k}] EN: {v}\n  VI: {dst.get(k)}")
