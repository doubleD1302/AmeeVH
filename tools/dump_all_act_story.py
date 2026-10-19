import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00727_0x789e881d02a7ddcb.bin', 'r', encoding='utf-8') as f:
    cn_act = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    act = json.load(f)['ActivityStory']

print("=== ALL ACTIVITY STORY ===")
for it in act:
    k = it['key']
    en = it['en']
    cn = cn_act.get(k, '')
    vi = it['vi_current']
    if len(en) > 3:
        print(f"[{k}] EN: {en} | CN: {cn} | VI: {vi}")
