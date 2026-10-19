import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00815_0x6f0361474c111904.bin', 'r', encoding='utf-8') as f:
    cn_mall = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['MallPackage']

print(f"Total entries in MallPackage: {len(p3)}")
for it in p3[:30]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_mall.get(k, '')
    print(f"[{k}]")
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}")
