import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00765_0x733ee8fdb8a6a976.bin', 'r', encoding='utf-8') as f:
    cn_dchar = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    dchar = json.load(f)['DatingCharacterEvent']

print("=== DATING CHARACTER EVENT SAMPLES ===")
for i, it in enumerate(dchar):
    if i % 25 == 0:
        k = it['key']
        en = it['en']
        cn = cn_dchar.get(k, '')
        vi = it['vi_current']
        print(f"[{k}]")
        print(f"  EN: {en}")
        print(f"  CN: {cn}")
        print(f"  VI: {vi}\n")
