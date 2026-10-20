import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

# Search interesting phrases
patterns = [
    r'haunt', r'deal', r'win win', r'come sunrise', r'no turning back',
    r'cost of', r'servant', r'turning back', r'reluctant', r'speech',
    r'cut off', r'ring', r'brawl', r'beat to death', r'senator',
    r'senate', r'coerced', r'evidence', r'innocent', r'treason',
    r'conspiracy', r'vermin', r'scum', r'pawn', r'bishop', r'rook',
    r'knight', r'queen', r'king', r'checkmate', r'chessboard',
    r'chess', r'scheme', r'barracks', r'capital', r'throne',
    r'seal of grace', r'company court', r'conviction', r'resolution'
]

for pat in patterns:
    matches = []
    reg = re.compile(r'\b' + pat, re.IGNORECASE)
    for k, v in src.items():
        if reg.search(v):
            matches.append((k, v, dst.get(k, '')))
    if matches:
        print(f"=== Pattern '{pat}': {len(matches)} matches ===")
        for m in matches[:3]:
            print(f"[{m[0]}]\n  SRC: {m[1]}\n  DST: {m[2]}")
