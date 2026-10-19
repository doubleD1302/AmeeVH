import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00719_0x6685539fd40c9e98.bin', 'r', encoding='utf-8') as f:
    cn_goods = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['ActivityGoods']

print(f"Total ActivityGoods items: {len(p3)}")
names = [it for it in p3 if it['key'].endswith('.1')]
descs = [it for it in p3 if it['key'].endswith('.2')]

print(f"Names: {len(names)}, Descs: {len(descs)}")

clunky_in_goods = []
for it in descs:
    vi = it['vi_current']
    en = it['en']
    cn = cn_goods.get(it['key'], '')
    if any(w in vi.lower() for w in ['được sử dụng', 'có thể được', 'được áp dụng', 'người bạn đồng hành', 'nguyên liệu cao cấp', 'biểu tượng ngôi sao', 'máy đánh bóng', 'cầu thang đá', 'express']):
        clunky_in_goods.append((it['key'], en, cn, vi))

print(f"Found {len(clunky_in_goods)} clunky items in ActivityGoods descs:")
for k, en, cn, vi in clunky_in_goods[:15]:
    print(f"[{k}]")
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}\n")
