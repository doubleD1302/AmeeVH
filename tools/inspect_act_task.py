import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00728_0xc316bcdb179b0d6e.bin', 'r', encoding='utf-8') as f:
    cn_act = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['ActivityTask']

print(f"Total entries in ActivityTask: {len(p3)}")
for it in p3[:30]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_act.get(k, '')
    print(f"[{k}]")
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}")
