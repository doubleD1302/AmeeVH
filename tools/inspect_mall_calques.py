import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00815_0x6f0361474c111904.bin', 'r', encoding='utf-8') as f:
    cn_mall = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    mall = json.load(f)['MallPackage']

print(f"Total mall items: {len(mall)}")

# Let's see what unique phrases exist in MallPackage
untranslated_or_calques = []
for it in mall:
    vi = it['vi_current']
    en = it['en']
    cn = cn_mall.get(it['key'], '')
    if any(w in vi for w in ['Siêu Trị', 'Cerulean', 'màu xanh da trời', 'Hàng Tuần Gói', 'Ưu Đãi Cầu Nguyện Gói']):
        untranslated_or_calques.append((it['key'], en, cn, vi))

print(f"Found {len(untranslated_or_calques)} items with calques:")
for k, en, cn, vi in untranslated_or_calques[:10]:
    print(f"  [{k}] EN: '{en}' | CN: '{cn}' | VI: '{vi}'")
