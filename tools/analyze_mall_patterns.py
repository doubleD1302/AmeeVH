import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00815_0x6f0361474c111904.bin', 'r', encoding='utf-8') as f:
    cn_mall = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['MallPackage']

print(f"Total MallPackage items: {len(p3)}")
unique_patterns = set()
for it in p3:
    en = it['en']
    cn = cn_mall.get(it['key'], '')
    vi = it['vi_current']
    if 'Trekker' in en or 'Boost' in en or 'Ticket' in en or 'Disc' in en:
        unique_patterns.add((en, cn, vi))

print(f"Matching sample patterns: {len(unique_patterns)}")
for en, cn, vi in sorted(list(unique_patterns))[:25]:
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}\n")
