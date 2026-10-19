import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00719_0x6685539fd40c9e98.bin', 'r', encoding='utf-8') as f:
    cn_goods = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    goods = json.load(f)['ActivityGoods']

names = [it for it in goods if it['key'].endswith('.1')]
unique_names = set((it['en'], cn_goods.get(it['key'], ''), it['vi_current']) for it in names)
print(f"Total names: {len(names)}, Unique: {len(unique_names)}")
for en, cn, vi in sorted(list(unique_names)):
    print(f"  EN: {en:35s} | CN: {cn:20s} | VI: {vi}")
