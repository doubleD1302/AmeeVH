import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

words_to_check = [
    r'drinks in', r'spores', r'parasite', r'ferment', r'cultivat',
    r'produce', r'production line', r'yield', r'crop', r'seed',
    r'root', r'shoot', r'sapling', r'vine', r'mandrake', r'nutrient',
    r'specimen', r'incubation', r'chamber', r'greenhouse'
]

for w in words_to_check:
    matches = []
    reg = re.compile(r'\b' + w, re.I)
    for k, v in src.items():
        if reg.search(v):
            matches.append((k, v, dst.get(k, '')))
    if matches:
        print(f"\n--- Checking '{w}' ({len(matches)} matches) ---")
        for m in matches[:3]:
            print(f"[{m[0]}]\n  SRC: {m[1]}\n  DST: {m[2]}")
