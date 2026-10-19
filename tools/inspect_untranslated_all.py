import json
from pathlib import Path

ROOT = Path('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa')
p3_tr = json.load(open(ROOT / 'work/batches/pillar3_translated.json', encoding='utf-8'))
p3_src = json.load(open(ROOT / 'work/batches/pillar3_story_dating_quests.json', encoding='utf-8'))

p4_tr = json.load(open(ROOT / 'work/batches/pillar4_translated.json', encoding='utf-8'))
p4_src = json.load(open(ROOT / 'work/batches/pillar4_system_gacha_shops.json', encoding='utf-8'))

print("=== PILLAR 3 INSPECTION ===")
for tbl, info in p3_tr.items():
    src_tbl = p3_src.get(tbl, {}).get('entries', {})
    for k, v in info.get('entries', {}).items():
        src_v = src_tbl.get(k, '')
        if v == src_v and any(c.isalpha() for c in src_v):
            print(f"[{tbl}.{k}] EN/Untranslated:\n  SRC: {src_v}\n  TR : {v}")

print("\n=== PILLAR 4 INSPECTION (Untranslated, non-DiscIP) ===")
for tbl, info in p4_tr.items():
    if tbl == 'DiscIP':
        continue
    src_tbl = p4_src.get(tbl, {}).get('entries', {})
    for k, v in info.get('entries', {}).items():
        src_v = src_tbl.get(k, '')
        if v == src_v and any(c.isalpha() for c in src_v):
            # check if it's English text (more than 1 word or English common word)
            print(f"[{tbl}.{k}] EN/Untranslated:\n  SRC: {src_v}\n  TR : {v}")
