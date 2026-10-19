import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00767_0x43ac532f7df5c82a.bin', 'r', encoding='utf-8') as f:
    cn_dland = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    dland = json.load(f)['DatingLandmarkEvent']

print("=== ALL DATING LANDMARK EVENT SAMPLES ===")
for i, it in enumerate(dland):
    k = it['key']
    en = it['en']
    cn = cn_dland.get(k, '')
    vi = it['vi_current']
    # show every 5th or interesting entries
    if i % 10 == 0:
        print(f"[{k}]")
        print(f"  EN: {en}")
        print(f"  CN: {cn}")
        print(f"  VI: {vi}\n")
