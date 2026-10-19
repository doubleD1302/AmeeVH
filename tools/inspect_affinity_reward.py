import json
from pathlib import Path
from collections import Counter

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00732_0xaa8312ae07d84ae0.bin', 'r', encoding='utf-8') as f:
    cn_aff = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['AffinityUpReward']

counts = Counter((it['en'], cn_aff.get(it['key'], ''), it['vi_current']) for it in p3)
print(f"Total entries in AffinityUpReward: {len(p3)}")
print(f"Unique (EN, CN, VI) triplets: {len(counts)}")
for (en, cn, vi), c in counts.most_common(30):
    print(f"  {c:3d}x | EN: {en:25s} | CN: {cn:20s} | VI: {vi}")
