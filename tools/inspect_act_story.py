import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00727_0x789e881d02a7ddcb.bin', 'r', encoding='utf-8') as f:
    cn_act = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['ActivityStory']

print("=== ACTIVITY STORY SAMPLES ===")
for it in p3[:30]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_act.get(k, '')
    if not (en.startswith('BT') or en.isdigit() or len(en) <= 3):
        print(f"[{k}]")
        print(f"  EN: {en}")
        print(f"  CN: {cn}")
        print(f"  VI: {vi}")
