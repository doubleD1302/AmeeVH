import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00767_0x43ac532f7df5c82a.bin', 'r', encoding='utf-8') as f:
    cn_dland = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['DatingLandmarkEvent']

print("=== DATING LANDMARK EVENT SAMPLES ===")
for it in p3[:15]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_dland.get(k, '')
    print(f"[{k}]")
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}")
